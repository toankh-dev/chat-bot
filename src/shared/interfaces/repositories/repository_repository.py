"""Repository Repository Interface for managing git repositories."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime


class IRepositoryRepository(ABC):
    """Interface for repository repository operations."""

    @abstractmethod
    def get_by_id(self, repository_id: int) -> Optional[any]:
        """
        Get repository by ID.

        Args:
            repository_id: Repository ID

        Returns:
            Repository model or None if not found
        """
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[any]:
        """
        Get repository by external ID (GitLab project ID).

        Args:
            external_id: External repository ID

        Returns:
            Repository model or None if not found
        """
        pass

    @abstractmethod
    def create(
        self,
        name: str,
        external_id: str,
        url: str,
        provider: str,
        default_branch: str,
        **kwargs
    ) -> any:
        """
        Create a new repository.

        Args:
            name: Repository name
            external_id: External repository ID
            url: Repository URL
            provider: Provider type (gitlab, github, etc.)
            default_branch: Default branch name
            **kwargs: Additional fields

        Returns:
            Created repository model
        """
        pass

    @abstractmethod
    def update(self, repository_id: int, **kwargs) -> Optional[any]:
        """
        Update repository.

        Args:
            repository_id: Repository ID
            **kwargs: Fields to update

        Returns:
            Updated repository model or None
        """
        pass

    @abstractmethod
    def delete(self, repository_id: int) -> bool:
        """
        Delete repository.

        Args:
            repository_id: Repository ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[any]:
        """
        List repositories by user.

        Args:
            user_id: User ID

        Returns:
            List of repository models
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
