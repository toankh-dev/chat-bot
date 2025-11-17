"""
Conversation API schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from schemas.chat_schema import MessageResponse


class ConversationResponse(BaseModel):
    """Response schema for a conversation."""
    id: int
    chatbot_id: int
    user_id: int
    title: Optional[str] = None
    status: str
    is_active: bool
    message_count: int
    started_at: str
    last_message_at: Optional[str] = None
    last_accessed_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "chatbot_id": 3,
                "user_id": 1,
                "title": "How can I integrate your API?",
                "status": "active",
                "is_active": True,
                "message_count": 10,
                "started_at": "2025-01-13T10:30:00.000Z",
                "last_message_at": "2025-01-13T10:35:00.000Z",
                "last_accessed_at": "2025-01-13T10:35:00.000Z"
            }
        }


class ConversationWithMessagesResponse(ConversationResponse):
    """Response schema for a conversation with messages."""
    messages: List[MessageResponse] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "chatbot_id": 3,
                "user_id": 1,
                "title": "How can I integrate your API?",
                "status": "active",
                "is_active": True,
                "message_count": 2,
                "started_at": "2025-01-13T10:30:00.000Z",
                "last_message_at": "2025-01-13T10:30:02.000Z",
                "last_accessed_at": "2025-01-13T10:30:02.000Z",
                "messages": [
                    {
                        "id": 123,
                        "role": "user",
                        "content": "How can I integrate your API?",
                        "created_at": "2025-01-13T10:30:00.000Z",
                        "metadata": {"token_count": 6}
                    },
                    {
                        "id": 124,
                        "role": "assistant",
                        "content": "To integrate the API, follow these steps...",
                        "created_at": "2025-01-13T10:30:02.000Z",
                        "metadata": {"token_count": 150, "model": "gemini-pro"}
                    }
                ]
            }
        }

