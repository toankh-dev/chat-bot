"""
Chat API schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID or null for new conversation")
    message: str = Field(..., min_length=1, description="User's message content")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": None,
                "message": "How can I integrate your API?"
            }
        }


class MessageResponse(BaseModel):
    """Response schema for a single message."""
    id: int
    role: str
    content: str
    created_at: str
    metadata: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "role": "user",
                "content": "How can I integrate your API?",
                "created_at": "2025-01-13T10:30:00.000Z",
                "metadata": {"token_count": 6}
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    conversation_id: int
    conversation_title: str
    user_message: MessageResponse
    assistant_message: MessageResponse

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "conversation_title": "How can I integrate your...",
                "user_message": {
                    "id": 123,
                    "role": "user",
                    "content": "How can I integrate your API?",
                    "created_at": "2025-01-13T10:30:00.000Z",
                    "metadata": {"token_count": 6}
                },
                "assistant_message": {
                    "id": 124,
                    "role": "assistant",
                    "content": "To integrate the API, follow these steps...",
                    "created_at": "2025-01-13T10:30:02.000Z",
                    "metadata": {"token_count": 150, "model": "gemini-pro"}
                }
            }
        }
