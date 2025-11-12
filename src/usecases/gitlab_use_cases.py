"""
GitLab use cases for repository management and synchronization.
Handles business logic for GitLab operations following Clean Architecture.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.gitlab_sync_service import GitLabSyncService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.connector_service import ConnectorService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository

logger = logging.getLogger(__name__)


class TestGitLabConnectionUseCase:
    """
    Use case for testing GitLab connectivity.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self) -> Dict[str, Any]:
        """
        Execute GitLab connection test use case.

        Returns:
            Test result with connection status and details
        """
        try:
            # Get GitLab connector
            gitlab_connector = self.connector_service.get_connector_by_provider("gitlab")
            if not gitlab_connector or not gitlab_connector.is_active:
                return {
                    "success": False,
                    "message": "GitLab connector not found or not active",
                    "details": {}
                }

            # Test connection
            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

            # Try to get user info to test connection
            try:
                user_info = gitlab_service.get_current_user()
                return {
                    "success": True,
                    "message": "GitLab connection successful",
                    "details": {
                        "user": user_info.get("username", "Unknown"),
                        "gitlab_url": gitlab_connector.config_schema.get("instance_config", {}).get("gitlab_url"),
                        "connector_id": gitlab_connector.id
                    }
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"GitLab connection failed: {str(e)}",
                    "details": {"error": str(e)}
                }

        except Exception as e:
            logger.error(f"Failed to test GitLab connection: {e}")
            return {
                "success": False,
                "message": f"Failed to test GitLab connection: {str(e)}",
                "details": {"error": str(e)}
            }


class FetchGitLabRepositoriesUseCase:
    """
    Use case for fetching repositories from GitLab.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, per_page: int = 20, page: int = 1) -> Dict[str, Any]:
        """
        Execute fetch GitLab repositories use case.

        Args:
            per_page: Number of repositories per page
            page: Page number to fetch

        Returns:
            Repository list with pagination info
        """
        try:
            # Get GitLab connector and service
            gitlab_connector = self.connector_service.get_connector_by_provider("gitlab")
            if not gitlab_connector or not gitlab_connector.is_active:
                raise ValueError("GitLab connector not found or not active")

            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

            # Fetch repositories
            repositories = gitlab_service.get_projects(per_page=per_page, page=page)

            return {
                "success": True,
                "repositories": repositories,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": len(repositories) if repositories else 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise ValueError(f"Failed to fetch repositories: {e}")
