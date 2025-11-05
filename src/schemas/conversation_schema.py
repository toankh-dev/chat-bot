"""Conversation and message schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageCreate(BaseModel):
    """Message creation request."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Message response model."""
    id: int
    conversation_id: int
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Conversation creation request."""
    chatbot_id: int
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response model."""
    id: int
    chatbot_id: int
    user_id: int
    title: Optional[str]
    status: str
    is_active: bool
    message_count: int
    started_at: datetime
    last_message_at: Optional[datetime]
    last_accessed_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages."""
    messages: List[MessageResponse] = []
