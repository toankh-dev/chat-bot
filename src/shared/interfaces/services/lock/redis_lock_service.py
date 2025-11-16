"""GitLab Service Interface."""

from abc import ABC, abstractmethod
from typing import Generator, Optional


class IRedisLockService(ABC):
    """
    Distributed lock service using Redis.

    """

    @abstractmethod
    def acquire_lock(
        self, lock_key: str, timeout: Optional[int] = None, blocking: bool = False
    ) -> Generator[None, None, None]:
        """
        Acquire distributed lock with automatic release.
        """
        pass

    @abstractmethod
    def get_active_locks(self, pattern: str = "sync_lock:*") -> list:
        """
        Get list of active lock keys matching pattern.
        """
        pass

    @abstractmethod
    def clear_lock(self, lock_key: str) -> bool:
        """
        Manually clear/delete a lock (admin operation).
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check Redis connection health.
        """
        pass
