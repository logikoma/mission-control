from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Security, Depends, WebSocket, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional, Union
from datetime import datetime
import bcrypt
from app.core.database import get_session
from app.models.user_org import UserOrg
from app.models.organization import Organization
from app.models.user import User
from app.models.sub_agent import SubAgent
from app.models.task import Task
from app.models.channel import Channel
import uuid

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_org(org_slug: str, session: AsyncSession = Depends(get_session)) -> Organization:
    # This dependency assumes org_slug is in path
    # For websocket, we might not use this directly in dependency chain if arguments differ
    result = await session.execute(select(Organization).where(Organization.slug == org_slug))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

async def verify_sub_agent_scope(
    sub_agent: SubAgent,
    request: Request,
    session: AsyncSession
) -> bool:
    """
    Enforce scoped access for sub-agents:
    - Can access their assigned task
    - Can access channels belonging to their project
    - Cannot access any other resources (returns 404 to prevent enumeration)
    """
    path = request.url.path
    
    # Extract path parameters from the request
    # FastAPI makes these available in request.path_params
    path_params = request.path_params
    
    # Task access: Check if accessing the assigned task
    if "task_id" in path_params:
        task_id_str = path_params["task_id"]
        try:
            task_id = uuid.UUID(task_id_str)
            if task_id == sub_agent.task_id:
                return True
        except ValueError:
            pass
    
    # Channel access: Check if channel belongs to the sub-agent's project
    if "channel_id" in path_params:
        channel_id_str = path_params["channel_id"]
        try:
            channel_id = uuid.UUID(channel_id_str)
            result = await session.execute(
                select(Channel).where(Channel.id == channel_id)
            )
            channel = result.scalar_one_or_none()
            
            if channel and channel.project_id == sub_agent.project_id:
                return True
        except ValueError:
            pass
    
    # If accessing a list endpoint for tasks or channels, we need special handling
    # For now, deny list access to sub-agents (they should only access specific resources)
    if "/tasks" in path and "task_id" not in path_params:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if "/channels" in path and "channel_id" not in path_params:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Deny access to all other resources (404 to prevent enumeration)
    raise HTTPException(status_code=404, detail="Resource not found")


async def get_current_user(
    request: Request,
    api_key: str = Security(api_key_header),
    org_slug: str = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
) -> Union[User, SubAgent]:
    """
    Enhanced authentication supporting both regular users and sub-agents.
    
    - Regular users: UUID-based API keys
    - Sub-agents: sk_{uuid}_{secret} format with scoped access
    """
    # Note: org_slug param is actually the Organization object returned by get_current_org dependency
    org = org_slug 

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    token = api_key.replace("Bearer ", "").strip()
    
    # Check if this is a sub-agent key (starts with "sk_")
    if token.startswith("sk_"):
        # Parse sub-agent key: sk_{uuid}_{secret}
        parts = token.split("_")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid API Key format")
        
        try:
            sub_agent_id = uuid.UUID(parts[1])
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid API Key format")
        
        # Fetch sub-agent from database
        result = await session.execute(
            select(SubAgent).where(
                SubAgent.id == sub_agent_id,
                SubAgent.org_id == org.id
            )
        )
        sub_agent = result.scalar_one_or_none()
        
        if not sub_agent:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        # Check if terminated
        if sub_agent.terminated:
            raise HTTPException(status_code=401, detail="API Key has been revoked")
        
        # Check if expired
        if sub_agent.timeout_at < datetime.utcnow():
            # Auto-terminate expired key
            sub_agent.terminated = True
            sub_agent.terminated_at = datetime.utcnow()
            session.add(sub_agent)
            await session.commit()
            raise HTTPException(status_code=401, detail="API Key has expired")
        
        # Verify the key hash using bcrypt
        if not bcrypt.checkpw(token.encode('utf-8'), sub_agent.api_key_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        # Verify scope - this enforces resource-level access control
        await verify_sub_agent_scope(sub_agent, request, session)
        
        return sub_agent
    
    # Regular user authentication (UUID-based)
    try:
        user_id = uuid.UUID(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API Key format")

    stmt = select(UserOrg).where(
        UserOrg.user_id == user_id,
        UserOrg.org_id == org.id
    )
    result = await session.execute(stmt)
    user_org = result.scalar_one_or_none()
    
    if not user_org:
        raise HTTPException(status_code=403, detail="User not authorized for this organization")

    user_res = await session.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user


async def get_current_human_user(
    current_user: Union[User, SubAgent] = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is a human (not a sub-agent).
    Use this for endpoints that should not be accessible to sub-agents.
    """
    if isinstance(current_user, SubAgent):
        raise HTTPException(
            status_code=403,
            detail="This endpoint is not accessible to sub-agents"
        )
    return current_user

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    if not token:
        return None
    
    try:
        # Assuming token is user_id for POC
        user_id = uuid.UUID(token)
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user
    except ValueError:
        return None
