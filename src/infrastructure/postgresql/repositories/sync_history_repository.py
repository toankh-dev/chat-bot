"""
SyncHistory Repository - Database operations for sync history tracking.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from shared.interfaces.repositories.sync_history_repository import ISyncHistoryRepository
from infrastructure.postgresql.models.sync_history_model import SyncHistoryModel
from core.logger import logger


class SyncHistoryRepository(ISyncHistoryRepository):
    """Repository for managing sync history records."""

    def __init__(self, db_session: Session):
        """
        Initialize sync history repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def create(self, sync_history: SyncHistoryModel) -> SyncHistoryModel:
        """
        Create a new sync history record.

        Args:
            sync_history: SyncHistory model instance

        Returns:
            Created sync history
        """
        self.db_session.add(sync_history)
        self.db_session.commit()
        self.db_session.refresh(sync_history)
        return sync_history

    def get_by_id(self, sync_id: int) -> Optional[SyncHistoryModel]:
        """
        Get sync history by ID.

        Args:
            sync_id: Sync history ID

        Returns:
            SyncHistory model or None
        """
        return self.db_session.query(SyncHistoryModel).filter(
            SyncHistoryModel.id == sync_id
        ).first()

    def list_by_repository(
        self,
        repo_id: int,
        limit: int = 50
    ) -> List[SyncHistoryModel]:
        """
        List sync history for a repository.

        Args:
            repo_id: Repository ID
            limit: Maximum number of records to return

        Returns:
            List of SyncHistory models
        """
        return self.db_session.query(SyncHistoryModel).filter(
            SyncHistoryModel.repo_id == repo_id
        ).order_by(desc(SyncHistoryModel.started_at)).limit(limit).all()

    def get_latest_sync(self, repo_id: int) -> Optional[SyncHistoryModel]:
        """
        Get the most recent sync for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            Latest SyncHistory model or None
        """
        return self.db_session.query(SyncHistoryModel).filter(
            SyncHistoryModel.repo_id == repo_id
        ).order_by(desc(SyncHistoryModel.started_at)).first()

    def get_running_syncs(self) -> List[SyncHistoryModel]:
        """
        Get all currently running syncs.

        Returns:
            List of running SyncHistory models
        """
        return self.db_session.query(SyncHistoryModel).filter(
            SyncHistoryModel.status == "running"
        ).all()

    def update(self, sync_history: SyncHistoryModel) -> SyncHistoryModel:
        """
        Update sync history.

        Args:
            sync_history: SyncHistory model with updates

        Returns:
            Updated sync history
        """
        self.db_session.commit()
        self.db_session.refresh(sync_history)
        return sync_history

    def complete_sync(
        self,
        sync_id: int,
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> Optional[SyncHistoryModel]:
        """
        Mark sync as completed.

        Args:
            sync_id: Sync history ID
            status: Final status (completed, failed, partial)
            error_message: Error message if failed

        Returns:
            Updated sync history or None
        """
        sync = self.get_by_id(sync_id)
        if not sync:
            return None

        sync.status = status
        sync.completed_at = datetime.utcnow()
        if sync.started_at:
            duration = sync.completed_at - sync.started_at
            sync.duration_seconds = int(duration.total_seconds())
        if error_message:
            sync.error_message = error_message

        return self.update(sync)

    def increment_stats(
        self,
        sync_id: int,
        files_processed: int = 0,
        files_succeeded: int = 0,
        files_failed: int = 0,
        files_skipped: int = 0,
        embeddings_created: int = 0,
        embeddings_deleted: int = 0,
        batches_completed: int = 0,
        api_calls: int = 0
    ) -> Optional[SyncHistoryModel]:
        """
        Increment sync statistics.

        Args:
            sync_id: Sync history ID
            files_processed: Number of files processed
            files_succeeded: Number of files succeeded
            files_failed: Number of files failed
            files_skipped: Number of files skipped
            embeddings_created: Number of embeddings created
            embeddings_deleted: Number of embeddings deleted
            batches_completed: Number of batches completed
            api_calls: Number of API calls made

        Returns:
            Updated sync history or None
        """
        sync = self.get_by_id(sync_id)
        if not sync:
            return None

        sync.files_processed += files_processed
        sync.files_succeeded += files_succeeded
        sync.files_failed += files_failed
        sync.files_skipped += files_skipped
        sync.embeddings_created += embeddings_created
        sync.embeddings_deleted += embeddings_deleted
        sync.batches_completed += batches_completed
        sync.api_calls_made += api_calls

        return self.update(sync)

    def get_recent_failed_syncs(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[SyncHistoryModel]:
        """
        Get recent failed syncs.

        Args:
            hours: Look back this many hours
            limit: Maximum number of records

        Returns:
            List of failed SyncHistory models
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db_session.query(SyncHistoryModel).filter(
            and_(
                SyncHistoryModel.status == "failed",
                SyncHistoryModel.started_at >= since
            )
        ).order_by(desc(SyncHistoryModel.started_at)).limit(limit).all()

    def get_sync_statistics(self, repo_id: int) -> dict:
        """
        Get aggregate statistics for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        stats = self.db_session.query(
            func.count(SyncHistoryModel.id).label('total_syncs'),
            func.sum(SyncHistoryModel.files_succeeded).label('total_files_synced'),
            func.sum(SyncHistoryModel.embeddings_created).label('total_embeddings'),
            func.avg(SyncHistoryModel.duration_seconds).label('avg_duration')
        ).filter(
            SyncHistoryModel.repo_id == repo_id
        ).first()

        return {
            'total_syncs': stats.total_syncs or 0,
            'total_files_synced': stats.total_files_synced or 0,
            'total_embeddings': stats.total_embeddings or 0,
            'avg_duration_seconds': int(stats.avg_duration) if stats.avg_duration else 0
        }

    def cleanup_old_history(self, days: int = 90) -> int:
        """
        Delete old sync history records.

        Args:
            days: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db_session.query(SyncHistoryModel).filter(
            SyncHistoryModel.started_at < cutoff_date
        ).delete()
        self.db_session.commit()
        return deleted

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise

    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise
