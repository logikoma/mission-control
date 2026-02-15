from typing import Optional
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
import uuid
from .base import TimestampMixin, UUIDMixin


class SubAgent(UUIDMixin, TimestampMixin, table=True):
    """
    SubAgent represents an ephemeral sub-agent with scoped credentials.
    
    Key Security Features:
    - API key is only shown once at creation
    - Stored as bcrypt hash in database
    - Scoped to specific task and project channels
    - Auto-expires after timeout_at
    - Can be manually terminated
    """
    __tablename__ = "sub_agents"
    
    name: str = Field(description="Human-readable name for the sub-agent")
    api_key_hash: str = Field(description="Bcrypt hash of the full API key (sk_{id}_{secret})")
    
    # Scoping
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    task_id: uuid.UUID = Field(foreign_key="tasks.id", index=True)
    project_id: uuid.UUID = Field(foreign_key="projects.id", index=True)
    
    # Lifecycle
    timeout_at: datetime = Field(description="UTC timestamp when key expires")
    terminated: bool = Field(default=False, description="True if manually revoked")
    terminated_at: Optional[datetime] = Field(default=None, description="When the key was terminated")
    
    # Relationships (uncomment when needed)
    # org: "Organization" = Relationship(back_populates="sub_agents")
    # task: "Task" = Relationship(back_populates="sub_agents")
    # project: "Project" = Relationship(back_populates="sub_agents")
