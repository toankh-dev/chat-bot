"""
FileChangeHistory Repository - Database operations for file change tracking.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from infrastructure.postgresql.models.file_change_history_model import FileChangeHistoryModel


class FileChangeHistoryRepository:
    """Repository for managing file change history records."""

    def __init__(self, db_session: Session):
        """
        Initialize file change history repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def create(self, file_change: FileChangeHistoryModel) -> FileChangeHistoryModel:
        """
        Create a new file change history record.

        Args:
            file_change: FileChangeHistory model instance

        Returns:
            Created file change history
        """
        self.db_session.add(file_change)
        self.db_session.commit()
        self.db_session.refresh(file_change)
        return file_change

    def create_batch(self, file_changes: List[FileChangeHistoryModel]) -> None:
        """
        Create multiple file change records (bulk insert).

        Args:
            file_changes: List of FileChangeHistory model instances
        """
        self.db_session.bulk_save_objects(file_changes)
        self.db_session.commit()

    def get_by_id(self, change_id: int) -> Optional[FileChangeHistoryModel]:
        """
        Get file change by ID.

        Args:
            change_id: File change history ID

        Returns:
            FileChangeHistory model or None
        """
        return self.db_session.query(FileChangeHistoryModel).filter(
            FileChangeHistoryModel.id == change_id
        ).first()

    def get_file_history(
        self,
        repo_id: int,
        file_path: str,
        limit: int = 50
    ) -> List[FileChangeHistoryModel]:
        """
        Get change history for a specific file.

        Args:
            repo_id: Repository ID
            file_path: File path
            limit: Maximum number of records

        Returns:
            List of FileChangeHistory models
        """
        return self.db_session.query(FileChangeHistoryModel).filter(
            and_(
                FileChangeHistoryModel.repo_id == repo_id,
                FileChangeHistoryModel.file_path == file_path
            )
        ).order_by(desc(FileChangeHistoryModel.created_at)).limit(limit).all()

    def get_commit_changes(self, commit_id: int) -> List[FileChangeHistoryModel]:
        """
        Get all file changes for a commit.

        Args:
            commit_id: Commit ID

        Returns:
            List of FileChangeHistory models
        """
        return self.db_session.query(FileChangeHistoryModel).filter(
            FileChangeHistoryModel.commit_id == commit_id
        ).all()

    def get_pending_changes(
        self,
        repo_id: Optional[int] = None,
        limit: int = 100
    ) -> List[FileChangeHistoryModel]:
        """
        Get pending file changes.

        Args:
            repo_id: Filter by repository ID (optional)
            limit: Maximum number of records

        Returns:
            List of pending FileChangeHistory models
        """
        query = self.db_session.query(FileChangeHistoryModel).filter(
            FileChangeHistoryModel.sync_status == "pending"
        )

        if repo_id:
            query = query.filter(FileChangeHistoryModel.repo_id == repo_id)

        return query.order_by(FileChangeHistoryModel.created_at).limit(limit).all()

    def update(self, file_change: FileChangeHistoryModel) -> FileChangeHistoryModel:
        """
        Update file change history.

        Args:
            file_change: FileChangeHistory model with updates

        Returns:
            Updated file change history
        """
        self.db_session.commit()
        self.db_session.refresh(file_change)
        return file_change

    def mark_synced(
        self,
        change_id: int,
        process_time_ms: Optional[int] = None
    ) -> Optional[FileChangeHistoryModel]:
        """
        Mark file change as synced.

        Args:
            change_id: File change history ID
            process_time_ms: Processing time in milliseconds

        Returns:
            Updated file change history or None
        """
        change = self.get_by_id(change_id)
        if not change:
            return None

        change.sync_status = "synced"
        change.synced_at = datetime.utcnow()
        if process_time_ms:
            change.process_time_ms = process_time_ms

        return self.update(change)

    def mark_failed(
        self,
        change_id: int,
        error_type: str,
        error_message: str,
        retry_delay_seconds: int = 60
    ) -> Optional[FileChangeHistoryModel]:
        """
        Mark file change as failed and schedule retry.

        Args:
            change_id: File change history ID
            error_type: Error category
            error_message: Sanitized error message
            retry_delay_seconds: Base delay for exponential backoff

        Returns:
            Updated file change history or None
        """
        change = self.get_by_id(change_id)
        if not change:
            return None

        change.sync_status = "failed"
        change.error_type = error_type
        change.error_message = error_message[:500]  # Truncate
        change.retry_count += 1
        change.last_retry_at = datetime.utcnow()

        # Exponential backoff
        backoff_delay = retry_delay_seconds * (2 ** change.retry_count)
        change.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_delay)

        return self.update(change)

    def mark_skipped(self, change_id: int) -> Optional[FileChangeHistoryModel]:
        """
        Mark file change as skipped.

        Args:
            change_id: File change history ID

        Returns:
            Updated file change history or None
        """
        change = self.get_by_id(change_id)
        if not change:
            return None

        change.sync_status = "skipped"
        return self.update(change)

    def get_retry_candidates(self, limit: int = 100) -> List[FileChangeHistoryModel]:
        """
        Get file changes ready for retry.

        Args:
            limit: Maximum number of records

        Returns:
            List of FileChangeHistory models ready for retry
        """
        now = datetime.utcnow()
        return self.db_session.query(FileChangeHistoryModel).filter(
            and_(
                FileChangeHistoryModel.sync_status == "failed",
                FileChangeHistoryModel.next_retry_at <= now
            )
        ).order_by(FileChangeHistoryModel.next_retry_at).limit(limit).all()

    def get_stats_by_repository(self, repo_id: int) -> dict:
        """
        Get file change statistics for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        stats = self.db_session.query(
            FileChangeHistoryModel.sync_status,
            func.count(FileChangeHistoryModel.id).label('count'),
            func.sum(FileChangeHistoryModel.additions).label('total_additions'),
            func.sum(FileChangeHistoryModel.deletions).label('total_deletions')
        ).filter(
            FileChangeHistoryModel.repo_id == repo_id
        ).group_by(FileChangeHistoryModel.sync_status).all()

        result = {
            'by_status': {},
            'total_additions': 0,
            'total_deletions': 0
        }

        for status, count, additions, deletions in stats:
            result['by_status'][status] = count
            result['total_additions'] += additions or 0
            result['total_deletions'] += deletions or 0

        return result

    def get_most_changed_files(
        self,
        repo_id: int,
        limit: int = 10
    ) -> List[dict]:
        """
        Get files with most changes in a repository.

        Args:
            repo_id: Repository ID
            limit: Number of files to return

        Returns:
            List of dictionaries with file path and change count
        """
        from sqlalchemy import func

        results = self.db_session.query(
            FileChangeHistoryModel.file_path,
            func.count(FileChangeHistoryModel.id).label('change_count')
        ).filter(
            FileChangeHistoryModel.repo_id == repo_id
        ).group_by(
            FileChangeHistoryModel.file_path
        ).order_by(
            desc('change_count')
        ).limit(limit).all()

        return [
            {'file_path': path, 'change_count': count}
            for path, count in results
        ]

    def cleanup_old_history(self, days: int = 90) -> int:
        """
        Delete old file change history records.

        Args:
            days: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db_session.query(FileChangeHistoryModel).filter(
            FileChangeHistoryModel.created_at < cutoff_date
        ).delete()
        self.db_session.commit()
        return deleted
