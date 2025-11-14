"""Connector Repository Interface."""

from abc import ABC, abstractmethod
from typing import Any

from src.infrastructure.postgresql.models.commit_model import CommitModel

class ICommitRepository(ABC):
    """Interface for commit repository operations."""

    @abstractmethod
    def get_latest_full_sync_by_repo_id(self, repo_id: int) -> CommitModel:
        """
        Get the latest full sync commit for a repository.

        Args:
            repo_id: Repository database ID (not external ID)

        Returns:
            Latest full sync commit or None
        """
        pass

    @abstractmethod
    def create(self, repo_id: int, code_files: list) -> CommitModel:
        """
        Create a new commit.

        Args:
            repo_id: Repository database ID (not external ID)
            code_files: List of code files changed

        Returns:
            Created commit

        Raises:
            IntegrityError: If foreign key constraint fails
        """
        pass

    