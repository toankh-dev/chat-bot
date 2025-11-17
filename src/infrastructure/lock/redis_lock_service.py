"""
Redis-based distributed lock service for preventing concurrent operations.
"""

import redis
from contextlib import contextmanager
from typing import Optional, Generator
import logging

from core.config import settings
from core.errors import SyncInProgressError
from shared.interfaces.services.lock.redis_lock_service import IRedisLockService

logger = logging.getLogger(__name__)

class RedisLockService(IRedisLockService):
    """
    Distributed lock service using Redis.

    """

    def __init__(self):
        """
        Initialize Redis lock service.
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
        """
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
