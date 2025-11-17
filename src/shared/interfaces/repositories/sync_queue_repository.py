"""
ISyncQueueRepository interface - Contract for sync queue operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from infrastructure.postgresql.models.sync_queue_model import SyncQueueModel


class ISyncQueueRepository(ABC):
    """Interface for sync queue repository operations."""

    @abstractmethod
    def enqueue_batch(self, queue_items: List[SyncQueueModel]) -> None:
        """
        Add multiple items to sync queue (bulk insert).

        Args:
            queue_items: List of SyncQueue model instances
        """
        pass

    @abstractmethod
    def get_pending_batch(
        self, repo_id: Optional[int] = None, limit: int = 10
    ) -> List[SyncQueueModel]:
        """
        Get batch of pending items from queue.

        Args:
            repo_id: Filter by repository ID (optional)
            limit: Maximum number of items to return

        Returns:
            List of pending SyncQueue models
        """
        pass

    @abstractmethod
    def mark_processing(self, queue_ids: List[int]) -> None:
        """
        Mark items as currently being processed.

        Args:
            queue_ids: List of queue item IDs
        """
        pass

    @abstractmethod
    def mark_completed(self, queue_id: int) -> Optional[SyncQueueModel]:
        """
        Mark item as completed.

        Args:
            queue_id: Queue item ID

        Returns:
            Updated queue item or None
        """
        pass

    @abstractmethod
    def mark_failed(
        self, queue_id: int, error: str, retry_delay_seconds: int = 60
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
        pass

    @abstractmethod
    def count_pending_by_commit(self, commit_id: int) -> int:
        """
        Count pending items for a specific commit.

        Args:
            commit_id: Commit ID to check

        Returns:
            Number of pending items
        """
        pass
