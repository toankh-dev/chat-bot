"""
Lock Service Interface (Dependency Inversion Principle)

PURPOSE:
  Define contract for distributed locking mechanisms.
  Allows swapping implementations (Redis, DynamoDB, Memcached, etc.) without changing business logic.

CLEAN ARCHITECTURE:
  Domain/Use Case layers depend on this interface (abstraction).
  Infrastructure layer provides concrete implementations (RedisLockService, etc.).

DESIGN PRINCIPLES:
  - Interface Segregation: Single responsibility (distributed locking only)
  - Dependency Inversion: High-level modules depend on abstraction, not concrete Redis
  - Open/Closed: Open for extension (new implementations), closed for modification
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, Optional, Generator


class ILockService(ABC):
    """
    Abstract interface for distributed lock service.

    Implementations:
      - RedisLockService: Redis-based distributed locking (production)
      - InMemoryLockService: In-memory locking (testing/development)
      - DynamoDBLockService: AWS DynamoDB locking (alternative)

    Use Cases:
      - Prevent concurrent GitLab sync for same repo/branch
      - Prevent concurrent KB processing
      - Prevent concurrent document upload/processing
      - Any operation requiring mutual exclusion across processes
    """

    @abstractmethod
    @contextmanager
    def acquire_lock(
        self,
        lock_key: str,
        timeout: Optional[int] = None,
        blocking: bool = False
    ) -> Generator[None, None, None]:
        """
        Acquire distributed lock with automatic release.

        Args:
            lock_key: Unique lock identifier (e.g., "sync_lock:repo:123:branch:main")
            timeout: Lock timeout in seconds (auto-expire after timeout)
            blocking: If True, wait for lock; if False, raise immediately

        Yields:
            None: Control flow returns to caller while lock is held

        Raises:
            SyncInProgressError: If lock already held and blocking=False
            ConnectionError: If cannot connect to lock backend

        Usage:
            with lock_service.acquire_lock("sync_lock:repo:123"):
                # Critical section - lock held
                perform_sync_operation()
            # Lock automatically released here

        Lock Semantics:
            - Exclusive: Only one process can hold lock at a time
            - Timeout: Lock auto-expires after configured timeout
            - Non-blocking (default): Immediate failure if lock unavailable
            - Context manager: Pythonic with-statement for automatic cleanup
        """
        pass

    @abstractmethod
    def get_active_locks(self, pattern: str = "*") -> List[str]:
        """
        Get list of active lock keys matching pattern.

        Args:
            pattern: Lock key pattern (e.g., "sync_lock:*", "kb_lock:*")

        Returns:
            List of active lock keys

        Usage:
            # Get all active sync locks
            locks = service.get_active_locks("sync_lock:*")
            print(f"Active syncs: {locks}")

            # Get locks for specific repo
            locks = service.get_active_locks("sync_lock:repo:123:*")
        """
        pass

    @abstractmethod
    def clear_lock(self, lock_key: str) -> bool:
        """
        Manually clear/delete a lock (admin operation).

        Args:
            lock_key: Lock key to clear

        Returns:
            True if lock was cleared, False if lock didn't exist

        Usage:
            # Clear stuck lock manually (admin only)
            cleared = service.clear_lock("sync_lock:repo:123:branch:main")

        WARNING:
            Use with caution! Only clear locks you're certain are stuck.
            Clearing active locks can cause data corruption.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check lock backend connection health.

        Returns:
            True if lock backend is reachable and operational

        Usage:
            if not lock_service.health_check():
                logger.error("Lock service is down!")
                # Fallback to non-locked operation or retry
        """
        pass


class ILockServiceFactory(ABC):
    """
    Factory interface for creating lock service instances.

    Allows dependency injection of different lock implementations based on configuration.
    """

    @abstractmethod
    def create(self, provider: str = "redis") -> ILockService:
        """
        Create lock service instance based on provider.

        Args:
            provider: Lock backend provider ("redis", "dynamodb", "memory")

        Returns:
            ILockService implementation

        Raises:
            ValueError: If provider not supported

        Usage:
            factory = LockServiceFactory()
            lock_service = factory.create(provider="redis")
        """
        pass
