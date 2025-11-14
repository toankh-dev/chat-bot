"""
Repository Repository - Database operations for repository tracking.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from shared.interfaces.repositories.repository_repository import IRepositoryRepository
from infrastructure.postgresql.models.repository_model import RepositoryModel
from core.logger import logger


class RepositoryRepository(IRepositoryRepository):
    """Repository for managing repository records."""

    def __init__(self, db_session: Session):
        """
        Initialize repository repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def create(self, repository: RepositoryModel) -> RepositoryModel:
        """
        Create a new repository.

        Args:
            repository: Repository model instance

        Returns:
            Created repository
        """
        self.db_session.add(repository)
        self.db_session.commit()
        self.db_session.refresh(repository)
        return repository

    def get_by_id(self, repo_id: int) -> Optional[RepositoryModel]:
        """
        Get repository by ID.

        Args:
            repo_id: Repository ID

        Returns:
            Repository model or None
        """
        return self.db_session.query(RepositoryModel).filter(
            RepositoryModel.id == repo_id
        ).first()

    def get_or_create(
        self,
        connection_id: int,
        external_id: str,
        defaults: dict = None
    ) -> tuple[RepositoryModel, bool]:
        """
        Get existing repository or create new one.

        Args:
            connection_id: User connection ID
            external_id: External repository ID (GitLab project ID, GitHub repo ID)
            defaults: Default values if creating new repository

        Returns:
            Tuple of (repository, created) where created is True if new
        """
        repository = self.db_session.query(RepositoryModel).filter(
            and_(
                RepositoryModel.connection_id == connection_id,
                RepositoryModel.external_id == external_id
            )
        ).first()

        if repository:
            return repository, False

        # Create new repository
        repo_data = defaults or {}
        repository = RepositoryModel(
            connection_id=connection_id,
            external_id=external_id,
            **repo_data
        )
        return self.create(repository), True

    def get_by_connection_and_external_id(
        self,
        connection_id: int,
        external_id: str
    ) -> Optional[RepositoryModel]:
        """
        Get repository by connection and external ID.

        Args:
            connection_id: User connection ID
            external_id: External repository ID

        Returns:
            Repository model or None
        """
        return self.db_session.query(RepositoryModel).filter(
            and_(
                RepositoryModel.connection_id == connection_id,
                RepositoryModel.external_id == external_id
            )
        ).first()

    def list_by_connection(
        self,
        connection_id: int,
        only_active: bool = True
    ) -> List[RepositoryModel]:
        """
        List all repositories for a connection.

        Args:
            connection_id: User connection ID
            only_active: If True, return only active repositories

        Returns:
            List of Repository models
        """
        query = self.db_session.query(RepositoryModel).filter(
            RepositoryModel.connection_id == connection_id
        )

        if only_active:
            query = query.filter(RepositoryModel.is_active == True)

        return query.order_by(RepositoryModel.created_at.desc()).all()

    def list_user_repositories(self, user_id: int) -> List[RepositoryModel]:
        """
        List all repositories for a user (across all connections).

        Args:
            user_id: User ID

        Returns:
            List of Repository models
        """
        return self.db_session.query(RepositoryModel).join(
            RepositoryModel.connection
        ).filter(
            RepositoryModel.connection.has(user_id=user_id)
        ).order_by(RepositoryModel.created_at.desc()).all()

    def update(self, repository: RepositoryModel) -> RepositoryModel:
        """
        Update repository.

        Args:
            repository: Repository model with updates

        Returns:
            Updated repository
        """
        repository.updated_at = datetime.utcnow()
        self.db_session.commit()
        self.db_session.refresh(repository)
        return repository

    def update_sync_status(
        self,
        repo_id: int,
        status: str,
        last_synced_at: Optional[datetime] = None
    ) -> Optional[RepositoryModel]:
        """
        Update repository sync status.

        Args:
            repo_id: Repository ID
            status: Sync status (pending, syncing, completed, failed)
            last_synced_at: Last sync timestamp (optional)

        Returns:
            Updated repository or None
        """
        repository = self.get_by_id(repo_id)
        if not repository:
            return None

        repository.sync_status = status
        if last_synced_at:
            repository.last_synced_at = last_synced_at

        return self.update(repository)

    def mark_syncing(self, repo_id: int) -> Optional[RepositoryModel]:
        """
        Mark repository as currently syncing.

        Args:
            repo_id: Repository ID

        Returns:
            Updated repository or None
        """
        return self.update_sync_status(repo_id, "syncing")

    def mark_completed(
        self,
        repo_id: int,
        last_synced_at: Optional[datetime] = None
    ) -> Optional[RepositoryModel]:
        """
        Mark repository sync as completed.

        Args:
            repo_id: Repository ID
            last_synced_at: Last sync timestamp (defaults to now)

        Returns:
            Updated repository or None
        """
        if not last_synced_at:
            last_synced_at = datetime.utcnow()
        return self.update_sync_status(repo_id, "completed", last_synced_at)

    def mark_failed(self, repo_id: int) -> Optional[RepositoryModel]:
        """
        Mark repository sync as failed.

        Args:
            repo_id: Repository ID

        Returns:
            Updated repository or None
        """
        return self.update_sync_status(repo_id, "failed")

    def delete(self, repo_id: int) -> bool:
        """
        Delete repository.

        Args:
            repo_id: Repository ID

        Returns:
            True if deleted, False if not found
        """
        repository = self.get_by_id(repo_id)
        if not repository:
            return False

        self.db_session.delete(repository)
        self.db_session.commit()
        return True

    def deactivate(self, repo_id: int) -> Optional[RepositoryModel]:
        """
        Deactivate a repository (soft delete).

        Args:
            repo_id: Repository ID

        Returns:
            Updated repository or None
        """
        repository = self.get_by_id(repo_id)
        if not repository:
            return None

        repository.is_active = False
        return self.update(repository)

    def get_pending_sync_repositories(self) -> List[RepositoryModel]:
        """
        Get repositories pending sync.

        Returns:
            List of repositories with sync_status = 'pending'
        """
        return self.db_session.query(RepositoryModel).filter(
            and_(
                RepositoryModel.is_active == True,
                RepositoryModel.sync_status == "pending"
            )
        ).order_by(RepositoryModel.created_at).all()

    def get_stale_syncing_repositories(
        self,
        stale_minutes: int = 60
    ) -> List[RepositoryModel]:
        """
        Get repositories stuck in 'syncing' status for too long.

        Args:
            stale_minutes: Minutes threshold for stale sync

        Returns:
            List of stale syncing repositories
        """
        stale_time = datetime.utcnow()
        # Subtract stale_minutes from current time
        from datetime import timedelta
        stale_time = stale_time - timedelta(minutes=stale_minutes)

        return self.db_session.query(RepositoryModel).filter(
            and_(
                RepositoryModel.sync_status == "syncing",
                RepositoryModel.updated_at < stale_time
            )
        ).all()