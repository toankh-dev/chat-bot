"""
UserGroup domain entity.

Represents the many-to-many relationship between users and groups.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class UserGroupEntity:
    """
    UserGroup entity representing the relationship between a user and a group.
    
    This is a junction table entity that manages the many-to-many
    relationship between users and groups.
    """
    
    id: Optional[int] = None
    user_id: int = 0
    group_id: int = 0
    created_at: Optional[datetime] = None
    added_by: Optional[int] = None  # User ID who added this user to the group
    
    def __post_init__(self):
        """Validate user-group relationship data after initialization."""
        if self.user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        
        if self.group_id <= 0:
            raise ValueError("Group ID must be a positive integer")

        if self.created_at is None:
            self.created_at = datetime.now(UTC)
    
    @property
    def is_persisted(self) -> bool:
        """Check if the user-group relationship has been persisted to database."""
        return self.id is not None
    
    def __str__(self) -> str:
        """String representation of the user-group relationship."""
        return f"UserGroup(user_id={self.user_id}, group_id={self.group_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the user-group relationship."""
        return (
            f"UserGroup(id={self.id}, user_id={self.user_id}, "
            f"group_id={self.group_id}, created_at={self.created_at}, "
            f"added_by={self.added_by})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on user_id and group_id."""
        if not isinstance(other, UserGroupEntity):
            return False
        return self.user_id == other.user_id and self.group_id == other.group_id
    
    def __hash__(self) -> int:
        """Hash based on user_id and group_id for use in sets/dicts."""
        return hash((self.user_id, self.group_id))


# Backwards compatibility alias
UserGroup = UserGroupEntity