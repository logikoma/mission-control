from typing import Optional, List, Any
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR, TSVECTOR
from sqlalchemy import Column, Index
import uuid
from .base import TimestampMixin, UUIDMixin

class Task(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_search_vector", "search_vector", postgresql_using="gin"),
    )
    
    title: str
    description: Optional[str] = None
    type: str = Field(default="chore")
    priority: str = Field(default="medium")
    status: str = Field(default="backlog")
    
    required_evidence_types: List[str] = Field(default_factory=list, sa_type=ARRAY(VARCHAR))
    
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)

    search_vector: Optional[Any] = Field(
        default=None, sa_column=Column(TSVECTOR)
    )
    
    # assignments: List["TaskProjectAssignment"] = Relationship(back_populates="task")
