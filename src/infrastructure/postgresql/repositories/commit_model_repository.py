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
        Get the latest full sync commit for a repository.

        Args:
            repo_id: Repository database ID (not external ID)

        Returns:
            Latest full sync commit or None

        """
        return (
            self.db_session.query(CommitModel)
            .filter(
                CommitModel.repo_id == repo_id,
                CommitModel.sha.like("full_sync_%")
            )
            .order_by(CommitModel.committed_at.desc())
            .first()
        )

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
