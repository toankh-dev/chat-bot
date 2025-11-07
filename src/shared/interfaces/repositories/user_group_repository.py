"""
User-Group repository interface.

Defines the contract for user-group relationship operations.
"""

from abc import ABC, abstractmethod
from typing import List
from domain.entities.group import Group

class UserGroupRepository(ABC):
    """
    User-Group repository interface.

    Manages the many-to-many relationship between users and groups.
    """

    @abstractmethod
    async def assign_user_to_groups(
        self, user_id: int, group_ids: List[int], added_by: int
    ) -> None:
        """
        Assign user to multiple groups.

        Args:
            user_id: User ID
            group_ids: List of group IDs
            added_by: Admin user ID who is making the assignment
        """
        pass

    @abstractmethod
    async def remove_user_from_all_groups(self, user_id: int) -> None:
        """
        Remove user from all groups.

        Args:
            user_id: User ID
        """
        pass

    @abstractmethod
    async def get_user_groups(self, user_id: int) -> List[Group]:
        """
        Get all groups a user belongs to.

        Args:
            user_id: User ID

        Returns:
            List of Group objects
        """
        pass

    @abstractmethod
    async def get_group_users(self, group_id: int) -> List[int]:
        """
        Get all user IDs in a group.

        Args:
            group_id: Group ID

        Returns:
            List of user IDs
        """
        pass
