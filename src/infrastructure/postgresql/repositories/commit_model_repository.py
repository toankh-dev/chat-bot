"""
Connector Repository - Database operations for connectors.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.logger import logger
from src.infrastructure.postgresql.models.commit_model import CommitModel
from src.shared.interfaces.repositories.commit_repository import ICommitRepository


class CommitRepository(ICommitRepository):
    """Repository for managing commit records."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize commit repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    async def get_latest_full_sync_by_repo_id(self, repo_id: int) -> CommitModel:
        """
        Get the latest synced commit for a repository.

        Args:
            repo_id: Repository database ID (not external ID)

        Returns:
            Latest commit or None

        Note:
            Returns any commit (real GitLab SHA or synthetic) ordered by committed_at.
            Use this to check if repository has been synced before.
        """
        stmt = (
            select(CommitModel)
            .where(CommitModel.repo_id == repo_id)
            .order_by(CommitModel.committed_at.desc())
            .limit(1)
        )

        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, repo_id: int, code_files: list) -> CommitModel:
        """
        Create a new commit with synthetic SHA (legacy method).

        Args:
            repo_id: Repository database ID (not external ID)
            code_files: List of code files changed

        Returns:
            Created commit
        """
        now = datetime.now(timezone.utc)
        sync_timestamp = now.isoformat()

        commit = CommitModel(
            repo_id=repo_id,
            external_id=f"full_sync_{sync_timestamp}",
            sha=f"full_sync_{sync_timestamp}",
            author_name="System",
            message="Full repository sync",
            committed_at=datetime.utcnow(),
            files_changed=len(code_files),
        )

        self.db_session.add(commit)
        await self.db_session.commit()
        await self.db_session.refresh(commit)
        return commit

    async def create_with_metadata(
        self,
        repo_id: int,
        sha: str,
        external_id: str,
        author_name: str,
        author_email: str,
        message: str,
        committed_at: datetime,
        files_changed: int
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
            committed_at: Commit timestamp from GitLab (timezone-aware or naive)
            files_changed: Number of files changed

        Returns:
            Created commit model
        """
        # Convert timezone-aware datetime to naive UTC for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
        if committed_at.tzinfo is not None:
            committed_at = committed_at.replace(tzinfo=None)

        commit = CommitModel(
            repo_id=repo_id,
            external_id=external_id,
            sha=sha,
            author_name=author_name,
            author_email=author_email,
            message=message,
            committed_at=committed_at,
            files_changed=files_changed,
        )

        self.db_session.add(commit)
        await self.db_session.commit()
        await self.db_session.refresh(commit)
        return commit

