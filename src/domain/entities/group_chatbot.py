"""
GroupChatbot domain entity.

Represents the many-to-many relationship between groups and chatbots.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class GroupChatbotEntity:
    """
    GroupChatbot entity representing the relationship between a group and a chatbot.
    
    This is a junction table entity that manages the many-to-many
    relationship between groups and chatbots.
    """
    
    id: Optional[int] = None
    group_id: int = 0
    chatbot_id: int = 0
    created_at: Optional[datetime] = None
    assigned_by: Optional[int] = None  # User ID who assigned this chatbot to the group
    
    def __post_init__(self):
        """Validate group-chatbot relationship data after initialization."""
        if self.group_id <= 0:
            raise ValueError("Group ID must be a positive integer")
        
        if self.chatbot_id <= 0:
            raise ValueError("Chatbot ID must be a positive integer")

        if self.created_at is None:
            self.created_at = datetime.now(UTC)
    
    @property
    def is_persisted(self) -> bool:
        """Check if the group-chatbot relationship has been persisted to database."""
        return self.id is not None
    
    def __str__(self) -> str:
        """String representation of the group-chatbot relationship."""
        return f"GroupChatbotEntity(group_id={self.group_id}, chatbot_id={self.chatbot_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the group-chatbot relationship."""
        return (
            f"GroupChatbotEntity(id={self.id}, group_id={self.group_id}, "
            f"chatbot_id={self.chatbot_id}, created_at={self.created_at}, "
            f"assigned_by={self.assigned_by})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on group_id and chatbot_id."""
        if not isinstance(other, (GroupChatbot, GroupChatbotEntity)):
            return False
        return self.group_id == other.group_id and self.chatbot_id == other.chatbot_id
    
    def __hash__(self) -> int:
        """Hash based on group_id and chatbot_id for use in sets/dicts."""
        return hash((self.group_id, self.chatbot_id))

# Backwards compatibility alias
GroupChatbot = GroupChatbotEntity