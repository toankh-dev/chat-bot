"""
Test ConnectorService functionality.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from application.services.connector_service import ConnectorService
from infrastructure.postgresql.models.connector_model import ConnectorModel
from infrastructure.postgresql.models.user_connection_model import UserConnectionModel
from infrastructure.external.gitlab_service import GitLabService


class TestConnectorService:
    """Test ConnectorService functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock(spec=Session)
        session.query.return_value.filter.return_value.first.return_value = None
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def connector_service(self, mock_db_session):
        """Create ConnectorService instance."""
        return ConnectorService(mock_db_session)

    def test_get_connector_not_found(self, connector_service, mock_db_session):
        """Test get_connector when connector doesn't exist."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = connector_service.get_connector("gitlab")

        # Assert
        assert result is None
        assert "gitlab" in connector_service._connector_cache
        assert connector_service._connector_cache["gitlab"] is None

    def test_get_connector_found(self, connector_service, mock_db_session):
        """Test get_connector when connector exists."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.name = "GitLab"
        mock_connector.provider_type = "gitlab"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_connector

        # Execute
        result = connector_service.get_connector("gitlab")

        # Assert
        assert result == mock_connector
        assert connector_service._connector_cache["gitlab"] == mock_connector

    def test_get_connector_cached(self, connector_service):
        """Test get_connector returns cached result."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        connector_service._connector_cache["gitlab"] = mock_connector

        # Execute
        result = connector_service.get_connector("gitlab")

        # Assert
        assert result == mock_connector

    def test_get_or_create_gitlab_connector_exists(self, connector_service):
        """Test get_or_create_gitlab_connector when exists."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        connector_service._connector_cache["gitlab"] = mock_connector

        # Execute
        result = connector_service.get_or_create_gitlab_connector()

        # Assert
        assert result == mock_connector

    @patch('application.services.connector_service.settings')
    def test_get_or_create_gitlab_connector_creates_new(
        self, 
        mock_settings, 
        connector_service, 
        mock_db_session
    ):
        """Test get_or_create_gitlab_connector creates new connector."""
        # Setup
        mock_settings.GITLAB_URL = "https://gitlab.com"
        mock_settings.GITLAB_API_TOKEN = "token123"
        
        # Mock connector creation
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        def mock_add(obj):
            obj.id = 1
        mock_db_session.add.side_effect = mock_add
        mock_db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

        # Execute
        with patch('application.services.connector_service.ConnectorModel') as mock_model:
            mock_model.return_value = mock_connector
            result = connector_service.get_or_create_gitlab_connector()

        # Assert
        assert result == mock_connector
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch('application.services.connector_service.settings')
    @patch('application.services.connector_service.GitLabService')
    def test_get_gitlab_service_with_connector(
        self, 
        mock_gitlab_service_class,
        mock_settings, 
        connector_service
    ):
        """Test get_gitlab_service with connector config."""
        # Setup
        mock_settings.GITLAB_URL = "https://gitlab.com"
        mock_settings.GITLAB_API_TOKEN = "token123"
        
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.id = 1
        mock_connector.config_schema = {
            "gitlab_url": "https://custom-gitlab.com"
        }
        
        mock_service = Mock(spec=GitLabService)
        mock_gitlab_service_class.return_value = mock_service

        # Execute
        result = connector_service.get_gitlab_service(mock_connector)

        # Assert
        assert result == mock_service
        mock_gitlab_service_class.assert_called_once_with(
            gitlab_url="https://custom-gitlab.com",
            private_token="token123"
        )
        assert connector_service._gitlab_service_cache[1] == mock_service

    @patch('application.services.connector_service.settings')
    @patch('application.services.connector_service.GitLabService')
    def test_get_gitlab_service_fallback_to_settings(
        self, 
        mock_gitlab_service_class,
        mock_settings, 
        connector_service
    ):
        """Test get_gitlab_service falls back to settings."""
        # Setup
        mock_settings.GITLAB_URL = "https://gitlab.com"
        mock_settings.GITLAB_API_TOKEN = "token123"
        
        mock_service = Mock(spec=GitLabService)
        mock_gitlab_service_class.return_value = mock_service

        # Execute
        result = connector_service.get_gitlab_service(None)

        # Assert
        assert result == mock_service
        mock_gitlab_service_class.assert_called_once_with(
            gitlab_url="https://gitlab.com",
            private_token="token123"
        )

    def test_get_sync_config_with_connector(self, connector_service):
        """Test get_sync_config with connector."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.config_schema = {
            "sync_config": {
                "default_batch_size": 15,
                "max_file_size_mb": 8,
                "concurrent_batches": 3
            }
        }

        # Execute
        result = connector_service.get_sync_config(mock_connector)

        # Assert
        assert result["batch_size"] == 15
        assert result["max_file_size_mb"] == 8
        assert result["concurrent_batches"] == 3

    def test_get_sync_config_default(self, connector_service):
        """Test get_sync_config returns defaults."""
        # Execute
        result = connector_service.get_sync_config(None)

        # Assert
        assert result["batch_size"] == 10
        assert result["max_file_size_mb"] == 5
        assert result["concurrent_batches"] == 2

    def test_clear_cache(self, connector_service):
        """Test clear_cache functionality."""
        # Setup
        connector_service._connector_cache["gitlab"] = Mock()
        connector_service._gitlab_service_cache[1] = Mock()

        # Execute
        connector_service.clear_cache()

        # Assert
        assert len(connector_service._connector_cache) == 0
        assert len(connector_service._gitlab_service_cache) == 0

    def test_refresh_connector(self, connector_service, mock_db_session):
        """Test refresh_connector functionality."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        connector_service._connector_cache["gitlab"] = Mock()
        connector_service._gitlab_service_cache[1] = Mock()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_connector

        # Execute
        result = connector_service.refresh_connector("gitlab")

        # Assert
        assert result == mock_connector
        assert len(connector_service._gitlab_service_cache) == 0  # Cleared for gitlab

    def test_validate_connector_config_valid(self, connector_service):
        """Test validate_connector_config with valid config."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.id = 1
        mock_connector.provider_type = "gitlab"
        mock_connector.config_schema = {
            "gitlab_url": "https://gitlab.com"
        }

        # Execute
        result = connector_service.validate_connector_config(mock_connector)

        # Assert
        assert result is True

    def test_validate_connector_config_invalid_url(self, connector_service):
        """Test validate_connector_config with invalid URL."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.id = 1
        mock_connector.provider_type = "gitlab"
        mock_connector.config_schema = {
            "gitlab_url": "invalid-url"
        }

        # Execute
        result = connector_service.validate_connector_config(mock_connector)

        # Assert
        assert result is False

    def test_validate_connector_config_no_schema(self, connector_service):
        """Test validate_connector_config with no config schema."""
        # Setup
        mock_connector = Mock(spec=ConnectorModel)
        mock_connector.id = 1
        mock_connector.config_schema = None

        # Execute
        result = connector_service.validate_connector_config(mock_connector)

        # Assert
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])