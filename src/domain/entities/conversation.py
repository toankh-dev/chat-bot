"""
Conversation domain entity.

Represents a conversation in the core business logic, decoupled from persistence/ORM concerns.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from domain.entities.message import Message

@dataclass
class Conversation:
    id: str
    user_id: str
    chatbot_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[str] = None  # Use datetime in real implementation
    updated_at: Optional[str] = None
