"""
Base repository interface.

Defines common repository operations following the Repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')
ID = TypeVar('ID')


class BaseRepository(ABC, Generic[T, ID]):
    """
    Base repository interface for common CRUD operations.

    This interface defines the contract that all repositories must implement.
    """

    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """Find entity by ID."""
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Find all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        pass

    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if entity exists."""
        pass
