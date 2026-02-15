from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func, select
from app.core.database import get_session
from app.models.organization import Organization
from app.models.event import Event
from app.models.task import Task
from app.core.auth import get_current_org
from pydantic import BaseModel
from datetime import datetime, timedelta
import io

router = APIRouter()

class ReportResponse(BaseModel):
    content: str
    format: str = "markdown"
    generated_at: datetime

@router.get("/summary", response_model=ReportResponse)
async def generate_summary_report(
    days: int = Query(7, ge=1, le=30),
    format: str = Query("markdown", regex="^(markdown)$"),
    org: Organization = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
):
    """
    Generate a periodic summary report for the organization.
    Includes active tasks, recent events, and high-level analytics.
    """
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # 1. Fetch Analytics
    active_tasks_res = await session.execute(
        text("SELECT count(*) FROM tasks WHERE org_id = :org_id AND status != 'done' AND archived_at IS NULL"),
        {"org_id": org.id}
    )
    active_tasks_count = active_tasks_res.scalar() or 0
    
    completed_tasks_res = await session.execute(
        text("SELECT count(*) FROM tasks WHERE org_id = :org_id AND status = 'done' AND completed_at >= :since"),
        {"org_id": org.id, "since": since}
    )
    completed_tasks_count = completed_tasks_res.scalar() or 0
    
    # 2. Fetch Recent Events
    events_stmt = select(Event).where(
        Event.org_id == org.id,
        Event.timestamp >= since
    ).order_by(Event.timestamp.desc()).limit(20)
    
    events_res = await session.execute(events_stmt)
    recent_events = events_res.scalars().all()
    
    # 3. Fetch Active Tasks Details
    tasks_stmt = select(Task).where(
        Task.org_id == org.id,
        Task.status != 'done',
        Task.archived_at == None
    ).order_by(Task.priority.desc(), Task.created_at.desc()).limit(10)
    
    tasks_res = await session.execute(tasks_stmt)
    active_tasks_list = tasks_res.scalars().all()

    # Generate Markdown Report
    report_lines = []
    report_lines.append(f"# Organization Summary Report: {org.name}")
    report_lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append(f"**Period:** Last {days} days")
    report_lines.append("")
    
    report_lines.append("## 📊 Analytics Overview")
    report_lines.append(f"- **Active Tasks:** {active_tasks_count}")
    report_lines.append(f"- **Completed Tasks (last {days}d):** {completed_tasks_count}")
    # Sub-agent utilization could be added here if we had reliable data
    report_lines.append("")
    
    report_lines.append("## 📝 Active Tasks (Top 10)")
    if not active_tasks_list:
        report_lines.append("_No active tasks found._")
    else:
        report_lines.append("| Priority | Title | Status |")
        report_lines.append("|---|---|---|")
        for task in active_tasks_list:
            report_lines.append(f"| {task.priority} | {task.title} | {task.status} |")
    report_lines.append("")

    report_lines.append("## 🕒 Recent Events (Last 20)")
    if not recent_events:
        report_lines.append("_No recent events found._")
    else:
        for event in recent_events:
            timestamp_str = event.timestamp.strftime('%Y-%m-%d %H:%M')
            report_lines.append(f"- **{timestamp_str}** - `{event.type}` by {event.actor_type}")
            # Could add payload details if needed
    
    report_content = "\n".join(report_lines)
    
    return ReportResponse(
        content=report_content,
        format="markdown",
        generated_at=datetime.utcnow()
    )
