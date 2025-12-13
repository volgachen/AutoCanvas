"""
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class SessionStatus:
    """Session status constants"""
    ACTIVE = "active"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"


class MessageRole:
    """Message role constants"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Session(BaseModel):
    """Session model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = Field(default=SessionStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Message(BaseModel):
    """Message model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    create_time: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)
    role: str = Field(default=MessageRole.USER)
    content: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
