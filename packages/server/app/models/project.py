from typing import Optional, List, Any
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy import Column, Index
import uuid
from .base import TimestampMixin, UUIDMixin

class Project(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_search_vector", "search_vector", postgresql_using="gin"),
    )

    name: str
    description: Optional[str] = None
    stage: str = Field(default="definition")
    owner_id: Optional[uuid.UUID] = Field(foreign_key="users.id")
    links: dict = Field(default_factory=dict, sa_type=JSONB)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)

    search_vector: Optional[Any] = Field(
        default=None, sa_column=Column(TSVECTOR)
    )

    # tasks: List["TaskProjectAssignment"] = Relationship(back_populates="project")
    # members: List["ProjectUserAssignment"] = Relationship(back_populates="project")
