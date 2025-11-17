"""
Connector Repository - Database operations for connectors.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from core.logger import logger
from src.infrastructure.postgresql.models.commit_model import CommitModel
from src.shared.interfaces.repositories.commit_repository import ICommitRepository


class CommitRepository(ICommitRepository):
    """Repository for managing commit records."""

    def __init__(self, db_session: Session):
        """
        Initialize commit repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def get_latest_full_sync_by_repo_id(self, repo_id: int) -> CommitModel:
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
        return (
            self.db_session.query(CommitModel)
            .filter(CommitModel.repo_id == repo_id)
            .order_by(CommitModel.committed_at.desc())
            .first()
        )

    def create(self, repo_id: int, code_files: list) -> CommitModel:
        """
        Create a new commit with synthetic SHA (legacy method).

        Args:
            repo_id: Repository database ID (not external ID)
            code_files: List of code files changed

        Returns:
            Created commit

        Raises:
            IntegrityError: If foreign key constraint fails

        Note:
            DEPRECATED: Use create_with_metadata() for new code.
            This method creates commits with synthetic SHA pattern "full_sync_{timestamp}".
        """
        sync_timestamp = datetime.utcnow().isoformat()
        commit = CommitModel(
            repo_id=repo_id,  # Use database repo.id, not external_id
            external_id=f"full_sync_{sync_timestamp}",
            sha=f"full_sync_{sync_timestamp}",  # Make SHA unique
            author_name="System",
            message="Full repository sync",
            committed_at=datetime.utcnow(),
            files_changed=len(code_files),
        )
        self.db_session.add(commit)
        self.db_session.commit()
        self.db_session.refresh(commit)
        return commit

    def create_with_metadata(
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
            committed_at: Commit timestamp from GitLab
            files_changed: Number of files changed

        Returns:
            Created commit model

        Raises:
            IntegrityError: If SHA already exists or foreign key constraint fails
        """
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
        self.db_session.commit()
        self.db_session.refresh(commit)
        logger.info(f"Created commit {commit.id} with SHA {sha[:8]} for repo {repo_id}")
        return commit
