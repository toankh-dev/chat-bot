"""
Redis-based distributed lock service for preventing concurrent operations.

PURPOSE:
  Provide distributed locking mechanism to prevent race conditions in sync operations.
  Critical for preventing duplicate work and data corruption in concurrent scenarios.

USE CASES:
  - UC-LOCK-1: Prevent concurrent GitLab sync for same repo/branch
  - UC-LOCK-2: Prevent concurrent KB sync operations
  - UC-LOCK-3: Prevent concurrent document processing

ARCHITECTURE:
  Uses Redis as distributed lock store with automatic timeout/release.
  Lock keys format: {operation}_lock:{resource_type}:{resource_id}

DEPENDENCIES:
  - Redis server (configured via settings.REDIS_*)
  - core.config for Redis connection settings
  - core.errors for SyncInProgressError exception
"""

import redis
from contextlib import contextmanager
from typing import Optional, Generator
import logging

from core.config import settings
from core.errors import SyncInProgressError

logger = logging.getLogger(__name__)


class RedisLockService:
    """
    Distributed lock service using Redis.

    DESIGN PRINCIPLES:
      - Fail-fast: Raise error immediately if lock unavailable (non-blocking)
      - Auto-release: Lock timeout ensures eventual release even if process crashes
      - Context manager: Pythonic with-statement for automatic cleanup
      - Singleton per process: Reuse Redis connection pool

    LOCK SEMANTICS:
      - Exclusive: Only one process can hold lock at a time
      - Timeout: Lock auto-expires after configured timeout (default: 1 hour)
      - Non-blocking: Immediate failure if lock already held (no waiting)

    EXAMPLES:
        # Prevent concurrent sync
        lock_key = f"sync_lock:repo:{repo_id}:branch:{branch}"
        with redis_lock_service.acquire_lock(lock_key):
            # Perform sync operation
            sync_repository(...)

        # Handle lock conflict
        try:
            with redis_lock_service.acquire_lock(lock_key):
                sync_repository(...)
        except SyncInProgressError as e:
            return {"error": "Sync already in progress", "retry_after": 60}
    """

    def __init__(self):
        """
        Initialize Redis lock service.

        Connects to Redis server using config from settings.

        Raises:
            redis.exceptions.ConnectionError: If cannot connect to Redis
        """
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # Test connection
            self.redis_client.ping()

            logger.info(
                f"RedisLockService initialized successfully",
                extra={
                    "redis_host": settings.REDIS_HOST,
                    "redis_port": settings.REDIS_PORT,
                    "redis_db": settings.REDIS_DB,
                },
            )

        except redis.exceptions.ConnectionError as e:
            logger.error(
                f"Failed to connect to Redis: {e}",
                extra={
                    "redis_host": settings.REDIS_HOST,
                    "redis_port": settings.REDIS_PORT,
                },
            )
            raise

    @contextmanager
    def acquire_lock(
        self, lock_key: str, timeout: Optional[int] = None, blocking: bool = False
    ) -> Generator[None, None, None]:
        """
        Acquire distributed lock with automatic release.

        Args:
            lock_key: Unique lock identifier (e.g., "sync_lock:repo:123:branch:main")
            timeout: Lock timeout in seconds (default: REDIS_LOCK_TIMEOUT_SECONDS = 3600)
            blocking: If True, wait for lock; if False, raise immediately (default: False)

        Yields:
            None: Control flow returns to caller while lock is held

        Raises:
            SyncInProgressError: If lock already held and blocking=False

        Usage:
            with lock_service.acquire_lock("sync_lock:repo:123:branch:main"):
                # Critical section - lock held
                perform_sync_operation()
            # Lock automatically released here

        Lock Timeout Behavior:
            - If process crashes, lock auto-expires after {timeout} seconds
            - Prevents deadlocks from unexpected failures
            - Default: 1 hour (sufficient for large repo sync)

        Blocking vs Non-Blocking:
            - blocking=False (default): Fail immediately if lock unavailable
            - blocking=True: Wait indefinitely until lock available (use with caution)
        """
        timeout = timeout or settings.REDIS_LOCK_TIMEOUT_SECONDS
        lock = self.redis_client.lock(lock_key, timeout=timeout)

        # Try to acquire lock
        acquired = lock.acquire(blocking=blocking)

        if not acquired:
            logger.warning(
                f"Lock acquisition failed: lock already held",
                extra={"lock_key": lock_key, "blocking": blocking},
            )

            # Extract resource info from lock_key for error message
            # Format: sync_lock:repo:{repo_id}:branch:{branch}
            resource_id = lock_key.replace("sync_lock:", "")

            raise SyncInProgressError(
                resource_type="repository", resource_id=resource_id
            )

        logger.info(
            f"Lock acquired successfully",
            extra={
                "lock_key": lock_key,
                "timeout": timeout,
                "blocking": blocking,
            },
        )

        try:
            # Yield control to caller while lock is held
            yield

        finally:
            # Always release lock (even if exception occurred)
            try:
                lock.release()
                logger.info(
                    f"Lock released successfully", extra={"lock_key": lock_key}
                )

            except Exception as e:
                # Lock might have expired or already released
                logger.error(
                    f"Error releasing lock: {e}",
                    extra={"lock_key": lock_key, "error": str(e)},
                )

    def get_active_locks(self, pattern: str = "sync_lock:*") -> list:
        """
        Get list of active lock keys matching pattern.

        Args:
            pattern: Redis key pattern (default: all sync locks)

        Returns:
            List of active lock keys

        Usage:
            # Get all active sync locks
            locks = service.get_active_locks("sync_lock:*")
            print(f"Active locks: {locks}")

            # Get locks for specific repo
            locks = service.get_active_locks("sync_lock:repo:123:*")
        """
        try:
            keys = self.redis_client.keys(pattern)
            logger.debug(f"Found {len(keys)} active locks matching '{pattern}'")
            return keys

        except Exception as e:
            logger.error(f"Error getting active locks: {e}")
            return []

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
        try:
            deleted = self.redis_client.delete(lock_key)

            if deleted:
                logger.warning(
                    f"Lock manually cleared",
                    extra={"lock_key": lock_key, "operation": "admin_clear"},
                )
                return True
            else:
                logger.info(
                    f"Lock clear attempted but key not found",
                    extra={"lock_key": lock_key},
                )
                return False

        except Exception as e:
            logger.error(f"Error clearing lock: {e}", extra={"lock_key": lock_key})
            raise

    def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is reachable and operational

        Usage:
            if not lock_service.health_check():
                logger.error("Redis is down!")
        """
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
