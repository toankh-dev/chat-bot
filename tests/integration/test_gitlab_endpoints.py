"""
Integration tests for GitLab API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.is_active = True
    user.role = Mock()
    user.role.name = "admin"
    return user


@pytest.fixture
def auth_headers(mock_current_user):
    """Mock authentication headers."""
    # In real tests, you would generate a real JWT token
    # For now, we'll mock the dependency
    return {"Authorization": "Bearer fake-jwt-token"}


class TestGitLabTestEndpoint:
    """Test /api/v1/gitlab/test endpoint."""

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_service')
    def test_gitlab_connection_success(self, mock_get_gitlab_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test successful GitLab connection."""
        # Mock dependencies
        mock_get_user.return_value = mock_current_user

        mock_gitlab_service = Mock()
        mock_gitlab_service.gl = Mock()
        mock_gitlab_service.gl.user = Mock()
        mock_gitlab_service.gl.user.username = "testuser"
        mock_gitlab_service.gl.user.name = "Test User"
        mock_gitlab_service.gl.user.email = "test@gitlab.com"
        mock_gitlab_service.gitlab_url = "https://gitlab.com"
        mock_get_gitlab_service.return_value = mock_gitlab_service

        # Test
        response = client.get("/api/v1/gitlab/test", headers=auth_headers)

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["connection"] == "success"

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_service')
    def test_gitlab_connection_failure(self, mock_get_gitlab_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test GitLab connection failure."""
        mock_get_user.return_value = mock_current_user
        mock_get_gitlab_service.side_effect = Exception("Connection failed")

        response = client.get("/api/v1/gitlab/test", headers=auth_headers)

        assert response.status_code == 500


class TestSyncRepositoryEndpoint:
    """Test /api/v1/gitlab/sync endpoint."""

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_sync_service')
    def test_sync_repository_success(self, mock_get_sync_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test successful repository sync."""
        mock_get_user.return_value = mock_current_user

        # Mock sync service
        mock_sync_service = Mock()
        mock_sync_service.sync_repository = MagicMock()
        mock_sync_service.sync_repository.return_value = {
            "success": True,
            "repository": "test-repo",
            "branch": "main",
            "files_processed": 25,
            "files_failed": 0,
            "total_chunks": 25,
            "languages": {"python": 25},
            "total_lines": 1000,
            "total_bytes": 50000
        }
        mock_get_sync_service.return_value = mock_sync_service

        # Test
        payload = {
            "repo_url": "https://gitlab.com/user/test-repo",
            "branch": "main",
            "knowledge_base_id": "kb_gitlab",
            "group_id": "test-group",
            "domain": "general"
        }

        response = client.post("/api/v1/gitlab/sync", json=payload, headers=auth_headers)

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["repository"] == "test-repo"
        assert data["files_processed"] == 25

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_sync_service')
    def test_sync_repository_with_failures(self, mock_get_sync_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test repository sync with some file failures."""
        mock_get_user.return_value = mock_current_user

        mock_sync_service = Mock()
        mock_sync_service.sync_repository = MagicMock()
        mock_sync_service.sync_repository.return_value = {
            "success": True,
            "repository": "test-repo",
            "branch": "main",
            "files_processed": 20,
            "files_failed": 5,  # Some files failed
            "total_chunks": 20,
            "languages": {"python": 20},
            "total_lines": 800,
            "total_bytes": 40000
        }
        mock_get_sync_service.return_value = mock_sync_service

        payload = {
            "repo_url": "https://gitlab.com/user/test-repo",
            "branch": "main",
            "knowledge_base_id": "kb_gitlab",
            "group_id": "test-group"
        }

        response = client.post("/api/v1/gitlab/sync", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["files_failed"] == 5

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    def test_sync_repository_missing_required_fields(self, mock_get_user, client, mock_current_user, auth_headers):
        """Test sync with missing required fields."""
        mock_get_user.return_value = mock_current_user

        # Missing repo_url
        payload = {
            "branch": "main",
            "knowledge_base_id": "kb_gitlab",
            "group_id": "test-group"
        }

        response = client.post("/api/v1/gitlab/sync", json=payload, headers=auth_headers)

        assert response.status_code == 422  # Validation error


class TestWebhookPushEndpoint:
    """Test /api/v1/gitlab/webhook/push endpoint."""

    @patch('src.api.controllers.gitlab_controller.settings')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_service')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_sync_service')
    def test_webhook_push_success(self, mock_get_sync_service, mock_get_gitlab_service, mock_settings, client):
        """Test successful webhook push handling."""
        # Mock settings
        mock_settings.GITLAB_WEBHOOK_SECRET = "test-secret"
        mock_settings.KNOWLEDGE_BASE_GITLAB_ID = "kb_gitlab"

        # Mock GitLab service
        mock_gitlab_service = Mock()
        mock_gitlab_service.parse_push_event.return_value = {
            "event_type": "push",
            "repository": {
                "name": "test-repo",
                "url": "https://gitlab.com/user/test-repo"
            },
            "branch": "main",
            "after": "abc123def456",
            "commits": []
        }
        mock_gitlab_service.get_changed_files.return_value = ["src/main.py", "README.md"]
        mock_get_gitlab_service.return_value = mock_gitlab_service

        # Mock sync service (background task will be queued)
        mock_sync_service = Mock()
        mock_get_sync_service.return_value = mock_sync_service

        # Test
        payload = {
            "project": {
                "id": 123,
                "name": "test-repo",
                "path_with_namespace": "user/test-repo",
                "web_url": "https://gitlab.com/user/test-repo"
            },
            "ref": "refs/heads/main",
            "before": "000000",
            "after": "abc123def456",
            "commits": [],
            "user_name": "Test User",
            "user_email": "test@example.com",
            "user_username": "testuser"
        }

        response = client.post(
            "/api/v1/gitlab/webhook/push?webhook_token=test-secret",
            json=payload
        )

        # Verify
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["status"] == "accepted"
        assert data["repository"] == "test-repo"
        assert data["files_changed"] == 2

    @patch('src.api.controllers.gitlab_controller.settings')
    def test_webhook_push_invalid_token(self, mock_settings, client):
        """Test webhook with invalid token."""
        mock_settings.GITLAB_WEBHOOK_SECRET = "correct-secret"

        payload = {"project": {}, "commits": []}

        response = client.post(
            "/api/v1/gitlab/webhook/push?webhook_token=wrong-secret",
            json=payload
        )

        assert response.status_code == 401
        assert "Invalid webhook token" in response.json()["detail"]

    @patch('src.api.controllers.gitlab_controller.settings')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_service')
    def test_webhook_push_invalid_payload(self, mock_get_gitlab_service, mock_settings, client):
        """Test webhook with invalid payload."""
        mock_settings.GITLAB_WEBHOOK_SECRET = "test-secret"

        mock_gitlab_service = Mock()
        mock_gitlab_service.parse_push_event.side_effect = ValueError("Invalid payload")
        mock_get_gitlab_service.return_value = mock_gitlab_service

        payload = {"invalid": "data"}

        response = client.post(
            "/api/v1/gitlab/webhook/push?webhook_token=test-secret",
            json=payload
        )

        assert response.status_code == 500


class TestListRepositoriesEndpoint:
    """Test /api/v1/gitlab/repos endpoint."""

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_sync_service')
    def test_list_repositories_success(self, mock_get_sync_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test listing synced repositories."""
        mock_get_user.return_value = mock_current_user

        mock_sync_service = Mock()
        mock_sync_service.get_sync_status = MagicMock()
        mock_sync_service.get_sync_status.return_value = {
            "repositories": [
                {
                    "name": "repo1",
                    "url": "https://gitlab.com/user/repo1",
                    "status": "synced"
                },
                {
                    "name": "repo2",
                    "url": "https://gitlab.com/user/repo2",
                    "status": "synced"
                }
            ]
        }
        mock_get_sync_service.return_value = mock_sync_service

        response = client.get(
            "/api/v1/gitlab/repos?group_id=test-group",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetSyncStatusEndpoint:
    """Test /api/v1/gitlab/status/{group_id} endpoint."""

    @patch('src.api.controllers.gitlab_controller.get_current_user')
    @patch('src.api.controllers.gitlab_controller.get_gitlab_sync_service')
    def test_get_sync_status_success(self, mock_get_sync_service, mock_get_user, client, mock_current_user, auth_headers):
        """Test getting sync status for a group."""
        mock_get_user.return_value = mock_current_user

        mock_sync_service = Mock()
        mock_sync_service.get_sync_status = MagicMock()
        mock_sync_service.get_sync_status.return_value = {
            "group_id": "test-group",
            "status": "active",
            "repositories": [],
            "total_documents": 100,
            "last_sync": "2024-01-15T10:00:00Z"
        }
        mock_get_sync_service.return_value = mock_sync_service

        response = client.get(
            "/api/v1/gitlab/status/test-group",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == "test-group"
        assert data["total_documents"] == 100
