"""
IFileChangeHistoryRepository interface - Contract for file change tracking operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from infrastructure.postgresql.models.file_change_history_model import (
    FileChangeHistoryModel,
)


class IFileChangeHistoryRepository(ABC):
    """Interface for file change history repository operations."""

    @abstractmethod
    def create_batch(self, file_changes: List[FileChangeHistoryModel]) -> None:
        """
        Create multiple file change records (bulk insert).

        Args:
            file_changes: List of FileChangeHistory model instances
        """
        pass

    @abstractmethod
    def mark_synced(
        self, change_id: int, process_time_ms: Optional[int] = None
    ) -> Optional[FileChangeHistoryModel]:
        """
        Mark file change as synced.

        Args:
            change_id: File change history ID
            process_time_ms: Processing time in milliseconds

        Returns:
            Updated file change history or None
        """
        pass

    @abstractmethod
    def mark_skipped(self, change_id: int) -> Optional[FileChangeHistoryModel]:
        """
        Mark file change as skipped.

        Args:
            change_id: File change history ID

        Returns:
            Updated file change history or None
        """
        pass
