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
    Note: This is a junction table with composite primary key (user_id, group_id), no separate id column.
    """

    user_id: int
    group_id: int
    added_by: int  # User ID who added this user to the group (required)
    joined_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate user-group relationship data after initialization."""
        if self.user_id <= 0:
            raise ValueError("User ID must be a positive integer")

        if self.group_id <= 0:
            raise ValueError("Group ID must be a positive integer")

        if self.added_by <= 0:
            raise ValueError("added_by must be a positive integer")

        if self.joined_at is None:
            self.joined_at = datetime.now()

    @property
    def is_persisted(self) -> bool:
        """Check if the user-group relationship has been persisted to database."""
        # Junction table is considered persisted if it has user_id and group_id
        return self.user_id > 0 and self.group_id > 0
    
    def __str__(self) -> str:
        """String representation of the user-group relationship."""
        return f"UserGroup(user_id={self.user_id}, group_id={self.group_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the user-group relationship."""
        return (
            f"UserGroup(user_id={self.user_id}, "
            f"group_id={self.group_id}, joined_at={self.joined_at}, "
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