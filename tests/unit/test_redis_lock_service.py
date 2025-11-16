"""
Unit tests for RedisLockService.

Tests distributed locking functionality including:
- Lock acquisition and release
- Concurrent lock conflicts
- Lock timeout behavior
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import redis.exceptions

from infrastructure.lock.redis_lock_service import RedisLockService
from core.errors import SyncInProgressError


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    with patch('infrastructure.lock.redis_lock_service.redis.Redis') as mock:
        client = MagicMock()
        mock.return_value = client

        # Mock successful ping
        client.ping.return_value = True

        yield client


@pytest.fixture
def lock_service(mock_redis_client):
    """Create RedisLockService instance with mocked Redis."""
    return RedisLockService()


class TestRedisLockServiceInitialization:
    """Test RedisLockService initialization."""

    def test_init_success(self, mock_redis_client):
        """Test successful initialization."""
        service = RedisLockService()

        assert service.redis_client is not None
        mock_redis_client.ping.assert_called_once()

    def test_init_connection_failure(self):
        """Test initialization fails when Redis unavailable."""
        with patch('infrastructure.lock.redis_lock_service.redis.Redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            mock_client.ping.side_effect = redis.exceptions.ConnectionError("Connection refused")

            with pytest.raises(redis.exceptions.ConnectionError):
                RedisLockService()


class TestLockAcquisition:
    """Test lock acquisition and release."""

    def test_acquire_lock_success(self, lock_service, mock_redis_client):
        """Test successful lock acquisition and release."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True  # Lock acquired

        lock_key = "test_lock:repo:123"

        with lock_service.acquire_lock(lock_key):
            # Lock should be acquired
            mock_lock.acquire.assert_called_once_with(blocking=False)

        # Lock should be released after context exit
        mock_lock.release.assert_called_once()

    def test_acquire_lock_already_held(self, lock_service, mock_redis_client):
        """Test lock acquisition fails when already held."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = False  # Lock already held

        lock_key = "test_lock:repo:123"

        with pytest.raises(SyncInProgressError) as exc_info:
            with lock_service.acquire_lock(lock_key):
                pass

        # Check error message
        error = exc_info.value
        assert error.status_code == 409
        assert "Sync already in progress" in error.message
        assert lock_key.replace("test_lock:", "") in error.details["resource_id"]

    def test_acquire_lock_with_timeout(self, lock_service, mock_redis_client):
        """Test lock acquisition with custom timeout."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True

        lock_key = "test_lock:repo:456"
        custom_timeout = 7200  # 2 hours

        with lock_service.acquire_lock(lock_key, timeout=custom_timeout):
            pass

        # Verify lock created with custom timeout
        mock_redis_client.lock.assert_called_with(lock_key, timeout=custom_timeout)

    def test_acquire_lock_blocking(self, lock_service, mock_redis_client):
        """Test lock acquisition with blocking=True."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True

        lock_key = "test_lock:repo:789"

        with lock_service.acquire_lock(lock_key, blocking=True):
            pass

        # Verify lock.acquire called with blocking=True
        mock_lock.acquire.assert_called_with(blocking=True)


class TestLockRelease:
    """Test lock release behavior."""

    def test_lock_released_on_exception(self, lock_service, mock_redis_client):
        """Test lock is released even if exception occurs."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True

        lock_key = "test_lock:repo:999"

        with pytest.raises(ValueError):
            with lock_service.acquire_lock(lock_key):
                raise ValueError("Test exception")

        # Lock should still be released
        mock_lock.release.assert_called_once()

    def test_lock_release_error_handled(self, lock_service, mock_redis_client):
        """Test error during lock release is handled gracefully."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True
        mock_lock.release.side_effect = Exception("Release failed")

        lock_key = "test_lock:repo:111"

        # Should not raise exception even if release fails
        with lock_service.acquire_lock(lock_key):
            pass

        # Verify release was attempted
        mock_lock.release.assert_called_once()


class TestLockUtilities:
    """Test utility methods."""

    def test_get_active_locks(self, lock_service, mock_redis_client):
        """Test getting list of active locks."""
        mock_redis_client.keys.return_value = [
            "sync_lock:repo:123:branch:main",
            "sync_lock:repo:456:branch:develop"
        ]

        locks = lock_service.get_active_locks("sync_lock:*")

        assert len(locks) == 2
        assert "sync_lock:repo:123:branch:main" in locks
        mock_redis_client.keys.assert_called_with("sync_lock:*")

    def test_get_active_locks_empty(self, lock_service, mock_redis_client):
        """Test getting active locks when none exist."""
        mock_redis_client.keys.return_value = []

        locks = lock_service.get_active_locks("sync_lock:*")

        assert len(locks) == 0

    def test_clear_lock_success(self, lock_service, mock_redis_client):
        """Test manually clearing a lock."""
        mock_redis_client.delete.return_value = 1  # 1 key deleted

        lock_key = "sync_lock:repo:123:branch:main"
        result = lock_service.clear_lock(lock_key)

        assert result is True
        mock_redis_client.delete.assert_called_with(lock_key)

    def test_clear_lock_not_found(self, lock_service, mock_redis_client):
        """Test clearing non-existent lock."""
        mock_redis_client.delete.return_value = 0  # 0 keys deleted

        lock_key = "sync_lock:repo:nonexistent"
        result = lock_service.clear_lock(lock_key)

        assert result is False

    def test_health_check_success(self, lock_service, mock_redis_client):
        """Test Redis health check when healthy."""
        mock_redis_client.ping.return_value = True

        result = lock_service.health_check()

        assert result is True

    def test_health_check_failure(self, lock_service, mock_redis_client):
        """Test Redis health check when unhealthy."""
        mock_redis_client.ping.side_effect = redis.exceptions.ConnectionError("Connection lost")

        result = lock_service.health_check()

        assert result is False


class TestLockKeyFormats:
    """Test different lock key formats."""

    def test_repo_branch_lock_key(self, lock_service, mock_redis_client):
        """Test lock key for repo/branch combination."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True

        lock_key = "sync_lock:repo:123:branch:main"

        with lock_service.acquire_lock(lock_key):
            pass

        mock_redis_client.lock.assert_called_with(lock_key, timeout=3600)

    def test_kb_sync_lock_key(self, lock_service, mock_redis_client):
        """Test lock key for KB sync."""
        mock_lock = MagicMock()
        mock_redis_client.lock.return_value = mock_lock
        mock_lock.acquire.return_value = True

        lock_key = "kb_sync_lock:kb:5"

        with lock_service.acquire_lock(lock_key):
            pass

        mock_redis_client.lock.assert_called_with(lock_key, timeout=3600)
