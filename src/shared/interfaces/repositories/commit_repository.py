"""Connector Repository Interface."""

from abc import ABC, abstractmethod
import datetime
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

    @abstractmethod
    async def create_with_metadata(
        self,
        repo_id: int,
        sha: str,
        external_id: str,
        author_name: str,
        author_email: str,
        message: str,
        committed_at: datetime,
        files_changed: int,
    ) -> CommitModel:
        """
        Create a new commit with full GitLab metadata.

        Args:
            repo_id: Repository database ID
            sha: Real GitLab commit SHA (40 chars hex)
            external_id: External commit ID (usually same as SHA)
            author_name: Commit author name
            author_email: Commit author email
            message: Commit message
            committed_at: Commit timestamp from GitLab
            files_changed: Number of files changed

        Returns:
            Created commit model
        """
        pass
