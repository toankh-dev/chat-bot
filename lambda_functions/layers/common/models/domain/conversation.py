"""Conversation and Message domain models"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(str, Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """Message domain model"""
    id: Optional[int] = None
    conversation_id: int
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Conversation(BaseModel):
    """Conversation domain model"""
    id: Optional[int] = None
    chatbot_id: int
    user_id: int
    title: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    is_active: bool = True
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    message_count: int = 0

    # Relationships (populated when needed)
    chatbot_name: Optional[str] = None
    user_name: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MessageFeedback(BaseModel):
    """Message feedback model"""
    id: Optional[int] = None
    message_id: int
    user_id: int
    is_positive: bool
    is_reviewed: bool = False
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
