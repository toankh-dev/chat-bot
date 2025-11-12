"""Sync History Repository Interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime


class ISyncHistoryRepository(ABC):
    """Interface for sync history repository operations."""

    @abstractmethod
    def create(
        self,
        repository_id: int,
        status: str,
        started_at: datetime,
        **kwargs
    ) -> any:
        """
        Create a new sync history record.

        Args:
            repository_id: Repository ID
            status: Sync status
            started_at: Sync start time
            **kwargs: Additional fields

        Returns:
            Created sync history model
        """
        pass

    @abstractmethod
    def update(self, sync_id: int, **kwargs) -> Optional[any]:
        """
        Update sync history record.

        Args:
            sync_id: Sync history ID
            **kwargs: Fields to update

        Returns:
            Updated sync history model or None
        """
        pass

    @abstractmethod
    def get_by_id(self, sync_id: int) -> Optional[any]:
        """
        Get sync history by ID.

        Args:
            sync_id: Sync history ID

        Returns:
            Sync history model or None
        """
        pass

    @abstractmethod
    def get_latest_by_repository(self, repository_id: int) -> Optional[any]:
        """
        Get latest sync history for repository.

        Args:
            repository_id: Repository ID

        Returns:
            Latest sync history model or None
        """
        pass

    @abstractmethod
    def list_by_repository(
        self,
        repository_id: int,
        limit: int = 10
    ) -> List[any]:
        """
        List sync history for repository.

        Args:
            repository_id: Repository ID
            limit: Maximum number of records

        Returns:
            List of sync history models
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
