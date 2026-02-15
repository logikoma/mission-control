from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class EventBase(BaseModel):
    org_id: uuid.UUID
    type: str
    actor_id: Optional[uuid.UUID] = None
    actor_type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EventCreate(EventBase):
    pass

class EventRead(EventBase):
    id: uuid.UUID
    sequence_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
