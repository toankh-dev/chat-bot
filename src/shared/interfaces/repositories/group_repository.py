"""
Group repository interface.

Defines the contract for group data access operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.group import GroupEntity

class GroupRepository(BaseRepository[GroupEntity, int], ABC):
    """
    Group repository interface.

    Extends BaseRepository with group-specific operations.
    """

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[GroupEntity]:
        """
        Find group by name.

        Args:
            name: Group name

        Returns:
            Group if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_active_groups(self, skip: int = 0, limit: int = 100) -> List[GroupEntity]:
        """
        Find all groups (no status filter needed for groups).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of groups
        """
        pass
