"""
Schemas for streaming chat responses.
"""

from pydantic import BaseModel
from typing import Dict, Any, Literal, Optional


class StreamEvent(BaseModel):
    """
    Base streaming event.

    Attributes:
        type: Event type
        data: Event data payload
    """
    type: Literal[
        "start",
        "token",
        "tool_start",
        "tool_end",
        "agent_select",
        "agent_action",
        "agent_finish",
        "orchestrator_start",
        "orchestrator_done",
        "info",
        "done",
        "error"
    ]
    data: Dict[str, Any]


class ChatStreamRequest(BaseModel):
    """
    Request for streaming chat endpoint.

    Attributes:
        message: User message
        conversation_id: Optional existing conversation ID
    """
    message: str
    conversation_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Search GitLab for authentication code",
                "conversation_id": None
            }
        }
