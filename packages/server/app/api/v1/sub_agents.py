from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
import secrets
import bcrypt

from app.core.database import get_session
from app.core.auth import get_current_org, get_current_human_user
from app.core.events import broadcast_event
from app.models.organization import Organization
from app.models.user import User
from app.models.sub_agent import SubAgent
from app.models.task import Task
from app.models.project import Project
from app.models.assignments import TaskProjectAssignment


router = APIRouter()


# Request/Response Models
class CreateSubAgentRequest(BaseModel):
    name: str = Field(description="Human-readable name for the sub-agent")
    task_id: str = Field(description="UUID of the task this sub-agent is assigned to")
    timeout_hours: int = Field(default=24, ge=1, le=168, description="Hours until key expires (1-168)")


class CreateSubAgentResponse(BaseModel):
    """
    IMPORTANT: The api_key is returned ONLY ONCE.
    It cannot be retrieved again after this response.
    """
    id: str
    name: str
    task_id: str
    project_id: str
    timeout_at: datetime
    api_key: str = Field(description="Ephemeral API key (shown only once)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Task-123-SubAgent",
                "task_id": "660e8400-e29b-41d4-a716-446655440111",
                "project_id": "770e8400-e29b-41d4-a716-446655440222",
                "timeout_at": "2026-02-16T12:00:00Z",
                "api_key": "sk_550e8400-e29b-41d4-a716-446655440000_3x4mpl3s3cr3t"
            }
        }


class SubAgentInfoResponse(BaseModel):
    id: str
    name: str
    task_id: str
    project_id: str
    timeout_at: datetime
    terminated: bool
    terminated_at: Optional[datetime]
    created_at: datetime


class TerminateSubAgentResponse(BaseModel):
    message: str
    terminated_at: datetime


@router.post("", response_model=CreateSubAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_sub_agent(
    request: CreateSubAgentRequest,
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_human_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new sub-agent with scoped credentials.
    
    The sub-agent will:
    - Only access the specified task
    - Only access channels belonging to the task's project
    - Automatically expire after timeout_hours
    - Return a plaintext API key ONLY ONCE (format: sk_{id}_{random_secret})
    
    Security:
    - The full key is bcrypt-hashed before storage
    - Access to other tasks/projects returns 404 (no enumeration)
    """
    
    # Validate task exists and belongs to org
    task_uuid = uuid.UUID(request.task_id)
    task_result = await session.execute(
        select(Task).where(Task.id == task_uuid, Task.org_id == org.id)
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get project_id from task assignments
    assignment_result = await session.execute(
        select(TaskProjectAssignment).where(TaskProjectAssignment.task_id == task_uuid)
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not assigned to any project"
        )
    
    project_id = assignment.project_id
    
    # Validate project exists
    project_result = await session.execute(
        select(Project).where(Project.id == project_id, Project.org_id == org.id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Generate API key: sk_{uuid}_{random_secret}
    sub_agent_id = uuid.uuid4()
    secret = secrets.token_urlsafe(32)  # 256 bits of entropy
    api_key = f"sk_{sub_agent_id}_{secret}"
    
    # Hash the full API key with bcrypt
    api_key_hash = bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Calculate timeout
    timeout_at = datetime.utcnow() + timedelta(hours=request.timeout_hours)
    
    # Create SubAgent
    sub_agent = SubAgent(
        id=sub_agent_id,
        name=request.name,
        api_key_hash=api_key_hash,
        org_id=org.id,
        task_id=task_uuid,
        project_id=project_id,
        timeout_at=timeout_at,
        terminated=False
    )
    
    session.add(sub_agent)
    await session.commit()
    await session.refresh(sub_agent)
    
    # Log event
    await broadcast_event(
        session=session,
        org_id=org.id,
        event_type="sub_agent.created",
        payload={
            "sub_agent_id": str(sub_agent.id),
            "sub_agent_name": sub_agent.name,
            "task_id": str(task_uuid),
            "project_id": str(project_id),
            "timeout_at": timeout_at.isoformat(),
            "timeout_hours": request.timeout_hours
        },
        actor_id=current_user.id,
        actor_type="user"
    )
    
    return CreateSubAgentResponse(
        id=str(sub_agent.id),
        name=sub_agent.name,
        task_id=str(task_uuid),
        project_id=str(project_id),
        timeout_at=timeout_at,
        api_key=api_key  # Only shown once!
    )


@router.post("/{sub_agent_id}/terminate", response_model=TerminateSubAgentResponse)
async def terminate_sub_agent(
    sub_agent_id: str,
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_human_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Immediately revoke a sub-agent's API key.
    
    This sets the terminated flag, preventing any further authentication.
    """
    
    # Validate UUID
    try:
        sub_agent_uuid = uuid.UUID(sub_agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sub-agent ID format"
        )
    
    # Get sub-agent
    result = await session.execute(
        select(SubAgent).where(SubAgent.id == sub_agent_uuid, SubAgent.org_id == org.id)
    )
    sub_agent = result.scalar_one_or_none()
    
    if not sub_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-agent not found"
        )
    
    # Already terminated?
    if sub_agent.terminated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sub-agent already terminated"
        )
    
    # Terminate
    terminated_at = datetime.utcnow()
    sub_agent.terminated = True
    sub_agent.terminated_at = terminated_at
    
    session.add(sub_agent)
    await session.commit()
    
    # Log event
    await broadcast_event(
        session=session,
        org_id=org.id,
        event_type="sub_agent.terminated",
        payload={
            "sub_agent_id": str(sub_agent.id),
            "sub_agent_name": sub_agent.name,
            "task_id": str(sub_agent.task_id),
            "project_id": str(sub_agent.project_id),
            "terminated_at": terminated_at.isoformat()
        },
        actor_id=current_user.id,
        actor_type="user"
    )
    
    return TerminateSubAgentResponse(
        message="Sub-agent terminated successfully",
        terminated_at=terminated_at
    )


@router.get("/{sub_agent_id}", response_model=SubAgentInfoResponse)
async def get_sub_agent(
    sub_agent_id: str,
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_human_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get information about a sub-agent.
    
    Note: The API key cannot be retrieved after creation.
    """
    
    try:
        sub_agent_uuid = uuid.UUID(sub_agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sub-agent ID format"
        )
    
    result = await session.execute(
        select(SubAgent).where(SubAgent.id == sub_agent_uuid, SubAgent.org_id == org.id)
    )
    sub_agent = result.scalar_one_or_none()
    
    if not sub_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-agent not found"
        )
    
    return SubAgentInfoResponse(
        id=str(sub_agent.id),
        name=sub_agent.name,
        task_id=str(sub_agent.task_id),
        project_id=str(sub_agent.project_id),
        timeout_at=sub_agent.timeout_at,
        terminated=sub_agent.terminated,
        terminated_at=sub_agent.terminated_at,
        created_at=sub_agent.created_at
    )
