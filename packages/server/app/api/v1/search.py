from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_session
from app.models.organization import Organization
from app.core.auth import get_current_org
from pydantic import BaseModel
import uuid

router = APIRouter()

class SearchResult(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    snippet: Optional[str] = None
    score: float

@router.get("/", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1),
    type: Optional[str] = Query(None, regex="^(project|task|message)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org: Organization = Depends(get_current_org),
    session: AsyncSession = Depends(get_session)
):
    """
    Search across Projects, Tasks, and Messages.
    Weighted ranking: Projects > Tasks > Messages.
    """
    
    # Base query parts
    queries = []
    
    # Project Query
    if not type or type == "project":
        project_query = """
            SELECT 
                id, 
                'project' as type, 
                name as title, 
                description as snippet, 
                ts_rank_cd(search_vector, websearch_to_tsquery('english', :q)) * 3.0 as score
            FROM projects
            WHERE org_id = :org_id AND search_vector @@ websearch_to_tsquery('english', :q)
        """
        queries.append(project_query)

    # Task Query
    if not type or type == "task":
        task_query = """
            SELECT 
                id, 
                'task' as type, 
                title, 
                description as snippet, 
                ts_rank_cd(search_vector, websearch_to_tsquery('english', :q)) * 2.0 as score
            FROM tasks
            WHERE org_id = :org_id AND search_vector @@ websearch_to_tsquery('english', :q)
        """
        queries.append(task_query)

    # Message Query
    if not type or type == "message":
        message_query = """
            SELECT 
                id, 
                'message' as type, 
                content as title, 
                substring(content from 1 for 200) as snippet, 
                ts_rank_cd(search_vector, websearch_to_tsquery('english', :q)) * 1.0 as score
            FROM messages
            WHERE org_id = :org_id AND search_vector @@ websearch_to_tsquery('english', :q)
        """
        queries.append(message_query)

    if not queries:
        return []

    # Combine queries
    full_query = " UNION ALL ".join(queries) + " ORDER BY score DESC LIMIT :limit OFFSET :offset"
    
    result = await session.execute(
        text(full_query), 
        {"q": q, "org_id": org.id, "limit": limit, "offset": offset}
    )
    
    rows = result.fetchall()
    return [
        SearchResult(
            id=row.id,
            type=row.type,
            title=row.title,
            snippet=row.snippet,
            score=row.score
        ) for row in rows
    ]
