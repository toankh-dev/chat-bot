"""
Group domain entity.

Represents a group of users in the system.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional, List
from domain.value_objects.uuid_vo import UUID


@dataclass
class GroupEntity:
    """
    Group entity representing a collection of users.

    A group is used to organize users and manage access to chatbots
    and other resources collectively.
    """

    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None  # User ID who created the group

    def __post_init__(self):
        """Validate group data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Group name cannot be empty")

        if self.name != self.name.strip():
            self.name = self.name.strip()

    @property
    def is_persisted(self) -> bool:
        """Check if the group has been persisted to database."""
        return self.id is not None

    def update_info(self, name: Optional[str] = None):
        """
        Update group information.

        Args:
            name: New group name
            description: New group description
        """
        if name is not None:
            if not name.strip():
                raise ValueError("Group name cannot be empty")
            self.name = name.strip()

        self.updated_at = datetime.now()

    def __str__(self) -> str:
        """String representation of the group."""
        return f"Group(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the group."""
        return (
            f"Group(id={self.id}, name='{self.name}', "
            f"description='{self.description}', created_at={self.created_at})"
        )


# Backwards compatibility alias
Group = GroupEntity