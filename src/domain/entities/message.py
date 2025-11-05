"""
Message domain entity for conversations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from ..value_objects.uuid_vo import UUID


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageStatus(str, Enum):
    """Message status enumeration."""
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """
    Message entity representing a single message in a conversation.

    Attributes:
        id: Unique message identifier
        conversation_id: Parent conversation ID
        session_id: Session ID this message belongs to
        role: Message role (user, assistant, system, tool)
        content: Message content text
        status: Message processing status
        metadata: Additional message metadata
        tool_calls: Tool call information if any
        tool_results: Tool execution results if any
        tokens_used: Number of tokens consumed
        model_id: Model used to generate this message
        timestamp: Message creation timestamp
    """

    id: UUID
    conversation_id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    status: MessageStatus = MessageStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: Optional[list] = None
    tool_results: Optional[list] = None
    tokens_used: int = 0
    model_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate message invariants."""
        if not self.content and not self.tool_calls:
            raise ValueError("Message must have either content or tool calls")

    def mark_as_streaming(self) -> None:
        """Mark message as currently streaming."""
        self.status = MessageStatus.STREAMING

    def mark_as_completed(self, tokens_used: int = 0) -> None:
        """Mark message as completed."""
        self.status = MessageStatus.COMPLETED
        self.tokens_used = tokens_used

    def mark_as_failed(self, error_message: str) -> None:
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.metadata["error"] = error_message

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to message."""
        self.metadata[key] = value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "session_id": str(self.session_id),
            "role": self.role.value,
            "content": self.content,
            "status": self.status.value,
            "metadata": self.metadata,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "tokens_used": self.tokens_used,
            "model_id": self.model_id,
            "timestamp": self.timestamp.isoformat()
        }

    def to_bedrock_format(self) -> Dict[str, Any]:
        """Convert to AWS Bedrock message format."""
        message = {
            "role": self.role.value,
            "content": [{"text": self.content}]
        }
        return message
