"""
User repository interface.

Defines the contract for user data access operations.
"""

from abc import abstractmethod
from typing import Optional, List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.user import UserEntity


class UserRepository(BaseRepository[UserEntity, str]):
    """
    User repository interface.

    Defines operations specific to user entities beyond the base CRUD operations.
    """

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """
        Find user by email address.

        Args:
            email: User's email address

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_active_users(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        """
        Find all active users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active user entities
        """
        pass
