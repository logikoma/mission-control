from typing import Optional, List, Any
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TSVECTOR
import uuid

class Message(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_search_vector", "search_vector", postgresql_using="gin"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True, nullable=False)
    channel_id: uuid.UUID = Field(foreign_key="channels.id", index=True, nullable=False)
    sender_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    content: str = Field(nullable=False)
    mentions: List[uuid.UUID] = Field(default=[], sa_column=Column(ARRAY(UUID(as_uuid=True)), server_default="{}"))
    created_at: datetime = Field(primary_key=True, default_factory=datetime.utcnow, index=True)

    search_vector: Optional[Any] = Field(
        default=None, sa_column=Column(TSVECTOR)
    )
