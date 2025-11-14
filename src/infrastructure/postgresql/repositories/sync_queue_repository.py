"""
SyncQueue Repository - Database operations for sync queue management.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from infrastructure.postgresql.models.sync_queue_model import SyncQueueModel


class SyncQueueRepository:
    """Repository for managing sync queue records."""

    def __init__(self, db_session: Session):
        """
        Initialize sync queue repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def enqueue(self, queue_item: SyncQueueModel) -> SyncQueueModel:
        """
        Add item to sync queue.

        Args:
            queue_item: SyncQueue model instance

        Returns:
            Created queue item
        """
        self.db_session.add(queue_item)
        self.db_session.commit()
        self.db_session.refresh(queue_item)
        return queue_item

    def enqueue_batch(self, queue_items: List[SyncQueueModel]) -> None:
        """
        Add multiple items to sync queue (bulk insert).

        Args:
            queue_items: List of SyncQueue model instances
        """
        self.db_session.add_all(queue_items)
        self.db_session.commit()

    def get_by_id(self, queue_id: int) -> Optional[SyncQueueModel]:
        """
        Get queue item by ID.

        Args:
            queue_id: Queue item ID

        Returns:
            SyncQueue model or None
        """
        return self.db_session.query(SyncQueueModel).filter(
            SyncQueueModel.id == queue_id
        ).first()

    def get_pending_batch(
        self,
        repo_id: Optional[int] = None,
        limit: int = 10
    ) -> List[SyncQueueModel]:
        """
        Get batch of pending items from queue.

        Args:
            repo_id: Filter by repository ID (optional)
            limit: Maximum number of items to return

        Returns:
            List of pending SyncQueue models
        """
        query = self.db_session.query(SyncQueueModel).filter(
            SyncQueueModel.status == "pending"
        )

        if repo_id:
            query = query.filter(SyncQueueModel.repo_id == repo_id)

        return query.order_by(
            SyncQueueModel.priority.desc(),
            SyncQueueModel.created_at
        ).limit(limit).all()

    def get_retry_batch(self, limit: int = 10) -> List[SyncQueueModel]:
        """
        Get batch of failed items ready for retry.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of SyncQueue models ready for retry
        """
        now = datetime.utcnow()
        return self.db_session.query(SyncQueueModel).filter(
            and_(
                SyncQueueModel.status == "failed",
                SyncQueueModel.retry_count < SyncQueueModel.max_retries,
                or_(
                    SyncQueueModel.next_retry_at.is_(None),
                    SyncQueueModel.next_retry_at <= now
                )
            )
        ).order_by(SyncQueueModel.next_retry_at).limit(limit).all()

    def mark_processing(self, queue_ids: List[int]) -> None:
        """
        Mark items as currently being processed.

        Args:
            queue_ids: List of queue item IDs
        """
        self.db_session.query(SyncQueueModel).filter(
            SyncQueueModel.id.in_(queue_ids)
        ).update(
            {
                "status": "processing",
                "started_at": datetime.utcnow()
            },
            synchronize_session=False
        )
        self.db_session.commit()

    def mark_completed(self, queue_id: int) -> Optional[SyncQueueModel]:
        """
        Mark item as completed.

        Args:
            queue_id: Queue item ID

        Returns:
            Updated queue item or None
        """
        item = self.get_by_id(queue_id)
        if not item:
            return None

        item.status = "completed"
        item.completed_at = datetime.utcnow()
        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def mark_failed(
        self,
        queue_id: int,
        error: str,
        retry_delay_seconds: int = 60
    ) -> Optional[SyncQueueModel]:
        """
        Mark item as failed and schedule retry.

        Args:
            queue_id: Queue item ID
            error: Error message
            retry_delay_seconds: Base delay for exponential backoff

        Returns:
            Updated queue item or None
        """
        item = self.get_by_id(queue_id)
        if not item:
            return None

        item.status = "failed"
        item.last_error = error[:500]  # Truncate error
        item.retry_count += 1

        # Exponential backoff: delay * 2^retry_count
        backoff_delay = retry_delay_seconds * (2 ** item.retry_count)
        item.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_delay)

        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def reset_to_pending(self, queue_id: int) -> Optional[SyncQueueModel]:
        """
        Reset item back to pending status.

        Args:
            queue_id: Queue item ID

        Returns:
            Updated queue item or None
        """
        item = self.get_by_id(queue_id)
        if not item:
            return None

        item.status = "pending"
        item.started_at = None
        item.completed_at = None
        item.next_retry_at = None

        self.db_session.commit()
        self.db_session.refresh(item)
        return item

    def get_queue_status(self, repo_id: Optional[int] = None) -> dict:
        """
        Get queue status statistics.

        Args:
            repo_id: Filter by repository ID (optional)

        Returns:
            Dictionary with queue statistics
        """
        from sqlalchemy import func

        query = self.db_session.query(
            SyncQueueModel.status,
            func.count(SyncQueueModel.id).label('count')
        )

        if repo_id:
            query = query.filter(SyncQueueModel.repo_id == repo_id)

        results = query.group_by(SyncQueueModel.status).all()

        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }

        for status, count in results:
            status_counts[status] = count

        return status_counts

    def cleanup_completed(
        self,
        repo_id: Optional[int] = None,
        hours: int = 24
    ) -> int:
        """
        Delete completed queue items older than specified hours.

        Args:
            repo_id: Filter by repository ID (optional)
            hours: Delete items completed more than this many hours ago

        Returns:
            Number of items deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = self.db_session.query(SyncQueueModel).filter(
            and_(
                SyncQueueModel.status == "completed",
                SyncQueueModel.completed_at < cutoff_time
            )
        )

        if repo_id:
            query = query.filter(SyncQueueModel.repo_id == repo_id)

        deleted = query.delete()
        self.db_session.commit()
        return deleted

    def get_stuck_processing_items(
        self,
        stale_minutes: int = 30
    ) -> List[SyncQueueModel]:
        """
        Get items stuck in processing status.

        Args:
            stale_minutes: Consider items stale after this many minutes

        Returns:
            List of stuck SyncQueue models
        """
        stale_time = datetime.utcnow() - timedelta(minutes=stale_minutes)
        return self.db_session.query(SyncQueueModel).filter(
            and_(
                SyncQueueModel.status == "processing",
                SyncQueueModel.started_at < stale_time
            )
        ).all()

    def reset_stuck_items(self, stale_minutes: int = 30) -> int:
        """
        Reset stuck processing items back to pending.

        Args:
            stale_minutes: Consider items stale after this many minutes

        Returns:
            Number of items reset
        """
        stuck_items = self.get_stuck_processing_items(stale_minutes)
        for item in stuck_items:
            self.reset_to_pending(item.id)
        return len(stuck_items)

    def count_pending_by_commit(self, commit_id: int) -> int:
        """
        Count pending items for a specific commit.

        Args:
            commit_id: Commit ID to check

        Returns:
            Number of pending items
        """
        return self.db_session.query(SyncQueueModel).filter(
            and_(
                SyncQueueModel.commit_id == commit_id,
                SyncQueueModel.status == "pending"
            )
        ).count()
