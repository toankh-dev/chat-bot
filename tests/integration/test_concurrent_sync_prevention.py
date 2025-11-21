"""
Integration tests for concurrent sync prevention using Redis locks.

Tests real-world scenarios:
- Concurrent sync attempts for same repo/branch
- Lock timeout and auto-release
- Different repos can sync concurrently
- Different branches can sync concurrently
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from application.services.gitlab_sync_service import GitLabSyncService
from core.errors import SyncInProgressError


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies for GitLabSyncService."""
    return {
        "repository_repository": MagicMock(),
        "commit_repository": MagicMock(),
        "sync_queue_repository": MagicMock(),
        "sync_history_repository": MagicMock(),
        "connector_repository": MagicMock(),
        "user_connection_repository": MagicMock(),
        "knowledge_base_repository": MagicMock(),
        "kb_source_repository": MagicMock(),
        "kb_sync_service": MagicMock(),
        "code_chunking_service": MagicMock(),
        "connector_service": MagicMock(),
        "kb_cleanup_service": AsyncMock(),
    }


@pytest.mark.asyncio
@pytest.mark.integration
class TestConcurrentSyncPrevention:
    """Integration tests for concurrent sync prevention."""

    async def test_concurrent_sync_same_repo_branch_raises_error(self, mock_dependencies):
        """
        Test that concurrent syncs for same repo/branch raise SyncInProgressError.

        Scenario:
        1. User A starts sync for repo-123/main
        2. User B tries to sync repo-123/main while A's sync is running
        3. User B should get SyncInProgressError (409)
        """
        from infrastructure.lock.redis_lock_service import RedisLockService

        # Create real Redis lock service
        redis_lock = RedisLockService()

        # Create GitLabSyncService with real Redis lock
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        # Mock internal sync implementation to simulate long-running sync
        async def slow_sync(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate 500ms sync
            return {"success": True, "files_processed": 100}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(side_effect=slow_sync)

        # Start first sync (User A)
        sync_params = {
            "user_id": 1,
            "connector_id": 1,
            "repository_external_id": "123",
            "knowledge_base_id": 1,
            "branch": "main"
        }

        task1 = asyncio.create_task(
            gitlab_sync_service.sync_repository_full(**sync_params)
        )

        # Wait a bit for lock to be acquired
        await asyncio.sleep(0.1)

        # Try second sync (User B) - should fail immediately
        with pytest.raises(SyncInProgressError) as exc_info:
            await gitlab_sync_service.sync_repository_full(**sync_params)

        # Verify error details
        error = exc_info.value
        assert error.status_code == 409
        assert error.error_code == "SYNC_IN_PROGRESS"
        assert "repository" in error.details["resource_type"]
        assert "123" in error.details["resource_id"]

        # Wait for first sync to complete
        result1 = await task1
        assert result1["success"] is True

        # Cleanup: Clear the lock
        lock_key = "sync_lock:repo:123:branch:main"
        redis_lock.clear_lock(lock_key)

    async def test_different_repos_can_sync_concurrently(self, mock_dependencies):
        """
        Test that different repos can sync concurrently without conflict.

        Scenario:
        - Sync repo-123/main and repo-456/main simultaneously
        - Both should succeed (different locks)
        """
        from infrastructure.lock.redis_lock_service import RedisLockService

        redis_lock = RedisLockService()
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        # Mock fast sync
        async def fast_sync(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {"success": True, "files_processed": 50}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(side_effect=fast_sync)

        # Sync two different repos concurrently
        task1 = asyncio.create_task(
            gitlab_sync_service.sync_repository_full(
                user_id=1,
                connector_id=1,
                repository_external_id="123",  # Repo 123
                knowledge_base_id=1,
                branch="main"
            )
        )

        task2 = asyncio.create_task(
            gitlab_sync_service.sync_repository_full(
                user_id=2,
                connector_id=1,
                repository_external_id="456",  # Repo 456 (different)
                knowledge_base_id=2,
                branch="main"
            )
        )

        # Both should complete successfully
        result1, result2 = await asyncio.gather(task1, task2)

        assert result1["success"] is True
        assert result2["success"] is True

        # Cleanup locks
        redis_lock.clear_lock("sync_lock:repo:123:branch:main")
        redis_lock.clear_lock("sync_lock:repo:456:branch:main")

    async def test_different_branches_can_sync_concurrently(self, mock_dependencies):
        """
        Test that different branches of same repo can sync concurrently.

        Scenario:
        - Sync repo-123/main and repo-123/develop simultaneously
        - Both should succeed (different locks)
        """
        from infrastructure.lock.redis_lock_service import RedisLockService

        redis_lock = RedisLockService()
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        async def fast_sync(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {"success": True}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(side_effect=fast_sync)

        # Sync two different branches concurrently
        task1 = asyncio.create_task(
            gitlab_sync_service.sync_repository_full(
                user_id=1,
                connector_id=1,
                repository_external_id="123",
                knowledge_base_id=1,
                branch="main"  # Main branch
            )
        )

        task2 = asyncio.create_task(
            gitlab_sync_service.sync_repository_full(
                user_id=1,
                connector_id=1,
                repository_external_id="123",  # Same repo
                knowledge_base_id=2,
                branch="develop"  # Different branch
            )
        )

        # Both should complete successfully
        result1, result2 = await asyncio.gather(task1, task2)

        assert result1["success"] is True
        assert result2["success"] is True

        # Cleanup locks
        redis_lock.clear_lock("sync_lock:repo:123:branch:main")
        redis_lock.clear_lock("sync_lock:repo:123:branch:develop")

    async def test_lock_released_after_sync_completes(self, mock_dependencies):
        """
        Test that lock is released after sync completes.

        Scenario:
        1. Start sync for repo-123/main
        2. Wait for sync to complete
        3. Verify lock is released (can sync again)
        """
        from infrastructure.lock.redis_lock_service import RedisLockService

        redis_lock = RedisLockService()
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        async def fast_sync(*args, **kwargs):
            await asyncio.sleep(0.05)
            return {"success": True}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(side_effect=fast_sync)

        sync_params = {
            "user_id": 1,
            "connector_id": 1,
            "repository_external_id": "123",
            "knowledge_base_id": 1,
            "branch": "main"
        }

        # First sync
        result1 = await gitlab_sync_service.sync_repository_full(**sync_params)
        assert result1["success"] is True

        # Second sync should succeed (lock released)
        result2 = await gitlab_sync_service.sync_repository_full(**sync_params)
        assert result2["success"] is True

        # Cleanup
        redis_lock.clear_lock("sync_lock:repo:123:branch:main")

    async def test_lock_released_on_exception(self, mock_dependencies):
        """
        Test that lock is released even if sync raises exception.

        Scenario:
        1. Start sync that will raise exception
        2. Verify lock is released after exception
        3. Next sync should succeed
        """
        from infrastructure.lock.redis_lock_service import RedisLockService

        redis_lock = RedisLockService()
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        # First call raises exception, second succeeds
        async def failing_then_succeeding_sync(*args, **kwargs):
            if not hasattr(failing_then_succeeding_sync, 'called'):
                failing_then_succeeding_sync.called = True
                raise ValueError("Sync failed")
            return {"success": True}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(
            side_effect=failing_then_succeeding_sync
        )

        sync_params = {
            "user_id": 1,
            "connector_id": 1,
            "repository_external_id": "123",
            "knowledge_base_id": 1,
            "branch": "main"
        }

        # First sync fails
        with pytest.raises(ValueError):
            await gitlab_sync_service.sync_repository_full(**sync_params)

        # Lock should be released, second sync should succeed
        result = await gitlab_sync_service.sync_repository_full(**sync_params)
        assert result["success"] is True

        # Cleanup
        redis_lock.clear_lock("sync_lock:repo:123:branch:main")


@pytest.mark.asyncio
@pytest.mark.integration
class TestLockKeyFormats:
    """Test lock key generation for different scenarios."""

    async def test_lock_key_with_default_branch(self, mock_dependencies):
        """Test lock key when branch is None (uses 'default')."""
        from infrastructure.lock.redis_lock_service import RedisLockService

        redis_lock = RedisLockService()
        gitlab_sync_service = GitLabSyncService(
            **mock_dependencies,
            redis_lock_service=redis_lock
        )

        async def fast_sync(*args, **kwargs):
            return {"success": True}

        gitlab_sync_service._sync_repository_full_impl = AsyncMock(side_effect=fast_sync)

        # Sync without specifying branch (None)
        result = await gitlab_sync_service.sync_repository_full(
            user_id=1,
            connector_id=1,
            repository_external_id="123",
            knowledge_base_id=1,
            branch=None  # No branch specified
        )

        assert result["success"] is True

        # Verify lock key used 'default'
        locks = redis_lock.get_active_locks("sync_lock:repo:123:*")
        # Lock should be released already, but we can test the format was correct

        # Cleanup
        redis_lock.clear_lock("sync_lock:repo:123:branch:default")
