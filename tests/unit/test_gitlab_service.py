"""
Unit tests for GitLabService.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.infrastructure.external.gitlab_service import GitLabService


@pytest.fixture
def mock_gitlab_client():
    """Mock GitLab client."""
    mock_gl = Mock()
    mock_gl.user = Mock()
    mock_gl.user.username = "test_user"
    mock_gl.user.name = "Test User"
    mock_gl.user.email = "test@example.com"
    return mock_gl


@pytest.fixture
def gitlab_service(mock_gitlab_client):
    """Create GitLabService with mocked client."""
    with patch('src.infrastructure.external.gitlab_service.gitlab.Gitlab', return_value=mock_gitlab_client):
        service = GitLabService(
            gitlab_url="https://gitlab.com",
            private_token="test-token"
        )
        service.gl = mock_gitlab_client
        return service


class TestGitLabServiceInit:
    """Test GitLabService initialization."""

    def test_init_with_valid_credentials(self, mock_gitlab_client):
        """Test initialization with valid credentials."""
        with patch('src.infrastructure.external.gitlab_service.gitlab.Gitlab', return_value=mock_gitlab_client):
            service = GitLabService(
                gitlab_url="https://gitlab.com",
                private_token="test-token"
            )

            assert service.gitlab_url == "https://gitlab.com"
            assert service.private_token == "test-token"
            assert service.gl is not None

    def test_init_authentication_failure(self):
        """Test initialization with authentication failure."""
        mock_gl = Mock()
        mock_gl.auth.side_effect = Exception("Authentication failed")

        with patch('src.infrastructure.external.gitlab_service.gitlab.Gitlab', return_value=mock_gl):
            with pytest.raises(Exception, match="Authentication failed"):
                GitLabService(
                    gitlab_url="https://gitlab.com",
                    private_token="invalid-token"
                )


class TestGetProjectInfo:
    """Test get_project_info method."""

    def test_get_project_info_success(self, gitlab_service, mock_gitlab_client):
        """Test getting project info successfully."""
        # Mock project
        mock_project = Mock()
        mock_project.id = 123
        mock_project.name = "test-repo"
        mock_project.path = "test-repo"
        mock_project.path_with_namespace = "user/test-repo"
        mock_project.description = "Test repository"
        mock_project.web_url = "https://gitlab.com/user/test-repo"
        mock_project.default_branch = "main"
        mock_project.created_at = "2024-01-01T00:00:00Z"
        mock_project.last_activity_at = "2024-01-15T00:00:00Z"

        mock_gitlab_client.projects.get.return_value = mock_project

        # Test
        result = gitlab_service.get_project_info("user/test-repo")

        # Verify
        assert result["id"] == 123
        assert result["name"] == "test-repo"
        assert result["path_with_namespace"] == "user/test-repo"
        assert result["default_branch"] == "main"

    def test_get_project_info_not_found(self, gitlab_service, mock_gitlab_client):
        """Test getting project info for non-existent project."""
        mock_gitlab_client.projects.get.side_effect = Exception("404 Project Not Found")

        with pytest.raises(ValueError, match="Failed to get project info"):
            gitlab_service.get_project_info("user/nonexistent")


class TestFilterCodeFiles:
    """Test filter_code_files method."""

    def test_filter_python_files(self, gitlab_service):
        """Test filtering Python files."""
        files = [
            "src/main.py",
            "tests/test_main.py",
            "README.md",
            "requirements.txt",
            "node_modules/package.js"
        ]

        result = gitlab_service.filter_code_files(files)

        assert "src/main.py" in result
        assert "README.md" in result
        assert "tests/test_main.py" not in result  # Excluded by pattern
        assert "requirements.txt" not in result  # Not a code file
        assert "node_modules/package.js" not in result  # Excluded by pattern

    def test_filter_javascript_files(self, gitlab_service):
        """Test filtering JavaScript files."""
        files = [
            "src/index.js",
            "src/app.tsx",
            "dist/bundle.min.js",
            "package-lock.json"
        ]

        result = gitlab_service.filter_code_files(files)

        assert "src/index.js" in result
        assert "src/app.tsx" in result
        assert "dist/bundle.min.js" not in result  # .min.js excluded
        assert "package-lock.json" not in result  # .lock excluded

    def test_filter_with_custom_extensions(self, gitlab_service):
        """Test filtering with custom extensions."""
        files = [
            "src/main.py",
            "src/app.js",
            "src/style.css"
        ]

        result = gitlab_service.filter_code_files(
            files,
            extensions=[".py"]
        )

        assert "src/main.py" in result
        assert "src/app.js" not in result
        assert "src/style.css" not in result

    def test_filter_empty_list(self, gitlab_service):
        """Test filtering empty file list."""
        result = gitlab_service.filter_code_files([])
        assert result == []


class TestParsePushEvent:
    """Test parse_push_event method."""

    def test_parse_push_event_success(self, gitlab_service):
        """Test parsing valid push event."""
        payload = {
            "project": {
                "id": 123,
                "name": "test-repo",
                "path_with_namespace": "user/test-repo",
                "web_url": "https://gitlab.com/user/test-repo"
            },
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "commits": [
                {
                    "id": "def456",
                    "message": "Add feature",
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com"
                    },
                    "timestamp": "2024-01-15T10:00:00Z",
                    "added": ["src/feature.py"],
                    "modified": ["README.md"],
                    "removed": []
                }
            ],
            "user_name": "Test User",
            "user_email": "test@example.com",
            "user_username": "testuser"
        }

        result = gitlab_service.parse_push_event(payload)

        assert result["event_type"] == "push"
        assert result["repository"]["name"] == "test-repo"
        assert result["branch"] == "main"
        assert result["after"] == "def456"
        assert len(result["commits"]) == 1
        assert result["commits"][0]["id"] == "def456"
        assert result["user"]["username"] == "testuser"

    def test_parse_push_event_invalid_payload(self, gitlab_service):
        """Test parsing invalid push event."""
        invalid_payload = {
            "project": {"name": "test-repo"}
            # Missing required fields
        }

        with pytest.raises(ValueError, match="Invalid push event payload"):
            gitlab_service.parse_push_event(invalid_payload)


class TestGetChangedFiles:
    """Test get_changed_files method."""

    def test_get_changed_files_success(self, gitlab_service):
        """Test extracting changed files from push event."""
        parsed_event = {
            "commits": [
                {
                    "added": ["src/new_file.py"],
                    "modified": ["src/existing.py", "README.md"],
                    "removed": ["src/old_file.py"]
                },
                {
                    "added": [],
                    "modified": ["src/existing.py"],  # Modified again
                    "removed": []
                }
            ]
        }

        result = gitlab_service.get_changed_files(parsed_event)

        # Should include added and modified, but not removed
        assert "src/new_file.py" in result
        assert "src/existing.py" in result
        assert "README.md" in result
        assert len(result) == 3  # No duplicates

    def test_get_changed_files_empty_commits(self, gitlab_service):
        """Test extracting from event with no commits."""
        parsed_event = {"commits": []}

        result = gitlab_service.get_changed_files(parsed_event)

        assert result == []


class TestValidateWebhookSignature:
    """Test validate_webhook_signature method."""

    def test_validate_signature_success(self, gitlab_service):
        """Test validating correct webhook signature."""
        secret = "my-secret-token"
        payload = b'{"event": "push"}'
        signature = "my-secret-token"  # GitLab uses simple token comparison

        result = gitlab_service.validate_webhook_signature(secret, payload, signature)

        assert result is True

    def test_validate_signature_failure(self, gitlab_service):
        """Test validating incorrect webhook signature."""
        secret = "my-secret-token"
        payload = b'{"event": "push"}'
        signature = "wrong-token"

        result = gitlab_service.validate_webhook_signature(secret, payload, signature)

        assert result is False


class TestExtractProjectPath:
    """Test _extract_project_path method."""

    def test_extract_from_https_url(self, gitlab_service):
        """Test extracting project path from HTTPS URL."""
        url = "https://gitlab.com/user/test-repo"

        result = gitlab_service._extract_project_path(url)

        assert result == "user/test-repo"

    def test_extract_from_http_url(self, gitlab_service):
        """Test extracting project path from HTTP URL."""
        url = "http://gitlab.example.com/group/subgroup/project"

        result = gitlab_service._extract_project_path(url)

        assert result == "group/subgroup/project"

    def test_extract_invalid_url(self, gitlab_service):
        """Test extracting from invalid URL."""
        url = "invalid-url"

        with pytest.raises(ValueError, match="Invalid repository URL"):
            gitlab_service._extract_project_path(url)


class TestCleanupClone:
    """Test cleanup_clone method."""

    def test_cleanup_existing_directory(self, gitlab_service):
        """Test cleaning up existing clone directory."""
        with patch('os.path.exists', return_value=True):
            with patch('shutil.rmtree') as mock_rmtree:
                gitlab_service.cleanup_clone("/tmp/test_clone")

                mock_rmtree.assert_called_once_with("/tmp/test_clone")

    def test_cleanup_nonexistent_directory(self, gitlab_service):
        """Test cleaning up non-existent directory."""
        with patch('os.path.exists', return_value=False):
            with patch('shutil.rmtree') as mock_rmtree:
                gitlab_service.cleanup_clone("/tmp/nonexistent")

                mock_rmtree.assert_not_called()
