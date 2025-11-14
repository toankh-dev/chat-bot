"""
Conversation domain entity.

Represents a conversation in the core business logic, decoupled from persistence/ORM concerns.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from domain.entities.message import Message

@dataclass
class ConversationEntity:
    user_id: int
    chatbot_id: int
    id: Optional[int] = None
    title: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    message_count: int = 0
    messages: List[Message] = field(default_factory=list)


# Backwards compatibility alias
Conversation = ConversationEntity
