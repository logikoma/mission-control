from typing import Optional, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, BigInteger, Identity, String
from .base import TimestampMixin, UUIDMixin
import uuid

class Event(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "events"

    # Monotonic ID for SSE replay
    sequence_id: int = Field(
        sa_column=Column(BigInteger, Identity(start=1, cycle=False), unique=True, index=True)
    )
    
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    type: str = Field(index=True)  # e.g., task.transitioned
    actor_id: Optional[uuid.UUID] = Field(foreign_key="users.id", nullable=True)
    actor_type: str = Field(default="system") # human | agent | system
    
    payload: dict = Field(default_factory=dict, sa_type=JSONB)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    # organization: "Organization" = Relationship(back_populates="events")
    # actor: Optional["User"] = Relationship(back_populates="events")

    # Override created_at/updated_at handling if timestamp is used instead
    # But TimestampMixin is fine for internal metadata
