"""
UserChatbot domain entity.

Represents the many-to-many relationship between users and chatbots.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class UserChatbotEntity:
    """
    UserChatbot entity representing the relationship between a user and a chatbot.
    
    This is a junction table entity that manages the many-to-many
    relationship between users and chatbots.
    """
    
    user_id: int
    chatbot_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    assigned_by: Optional[int] = None  # User ID who assigned this chatbot to the user
    
    def __post_init__(self):
        """Validate user-chatbot relationship data after initialization."""
        if self.user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        
        if self.chatbot_id <= 0:
            raise ValueError("Chatbot ID must be a positive integer")

        if self.created_at is None:
            self.created_at = datetime.now(UTC)
    
    @property
    def is_persisted(self) -> bool:
        """Check if the user-chatbot relationship has been persisted to database."""
        return self.id is not None
    
    def __str__(self) -> str:
        """String representation of the user-chatbot relationship."""
        return f"UserChatbot(user_id={self.user_id}, chatbot_id={self.chatbot_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the user-chatbot relationship."""
        return (
            f"UserChatbot(id={self.id}, user_id={self.user_id}, "
            f"chatbot_id={self.chatbot_id}, created_at={self.created_at}, "
            f"assigned_by={self.assigned_by})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on user_id and chatbot_id."""
        if not isinstance(other, UserChatbotEntity):
            return False
        return self.user_id == other.user_id and self.chatbot_id == other.chatbot_id
    
    def __hash__(self) -> int:
        """Hash based on user_id and chatbot_id for use in sets/dicts."""
        return hash((self.user_id, self.chatbot_id))


# Backwards compatibility alias
UserChatbot = UserChatbotEntity