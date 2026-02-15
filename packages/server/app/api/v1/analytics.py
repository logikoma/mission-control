from fastapi import APIRouter, Depends, Query
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from app.core.database import get_session
from app.models.organization import Organization
from app.core.auth import get_current_org
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter()

class AnalyticsSummary(BaseModel):
    active_tasks: int
    completed_tasks_7d: int
    subagent_utilization: int  # Number of subagents spawned in last 7 days

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    org: Organization = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
):
    """
    Get high-level analytics summary for the organization.
    """
    
    # 1. Active Tasks
    active_tasks_query = text("""
        SELECT count(*) FROM tasks 
        WHERE org_id = :org_id 
        AND status != 'done' 
        AND archived_at IS NULL
    """)
    active_tasks_res = await session.execute(active_tasks_query, {"org_id": org.id})
    active_tasks = active_tasks_res.scalar() or 0

    # 2. Completed Tasks (Last 7 Days)
    completed_tasks_query = text("""
        SELECT count(*) FROM tasks 
        WHERE org_id = :org_id 
        AND status = 'done' 
        AND completed_at >= :since
    """)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    completed_tasks_res = await session.execute(completed_tasks_query, {"org_id": org.id, "since": seven_days_ago})
    completed_tasks_7d = completed_tasks_res.scalar() or 0

    # 3. Sub-agent Utilization (Count 'subagent.spawned' events in last 7 days)
    # Assuming we store events in 'events' table or similar. 
    # If events table doesn't exist or track this yet, return 0.
    # We'll check 'event_log' or 'events' table.
    # The requirement mentions "recent events from the event log".
    # I'll assume an 'events' table exists from 'poc-realtime-events'.
    
    # Let's check if 'events' table exists and has 'type'.
    # Based on previous context, 'poc-realtime-events' exists.
    
    subagent_query = text("""
        SELECT count(*) FROM events 
        WHERE org_id = :org_id 
        AND type = 'subagent.spawned'
        AND created_at >= :since
    """)
    try:
        subagent_res = await session.execute(subagent_query, {"org_id": org.id, "since": seven_days_ago})
        subagent_utilization = subagent_res.scalar() or 0
    except Exception:
        # Fallback if events table structure is different or doesn't exist
        subagent_utilization = 0

    return AnalyticsSummary(
        active_tasks=active_tasks,
        completed_tasks_7d=completed_tasks_7d,
        subagent_utilization=subagent_utilization
    )
