"""
GitLab use cases for repository management and synchronization.
Handles business logic for GitLab operations following Clean Architecture.
"""

import logging
from typing import Dict, Any

from application.services.gitlab_sync_service import GitLabSyncService
from application.services.connector_service import ConnectorService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from schemas.gitlab_schema import SyncRepositoryRequest
from core.errors import BusinessRuleViolationError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class SyncRepositoryUseCase:
    """
    Use case for syncing GitLab repository to knowledge base.
    """

    def __init__(
        self,
        connector_service: ConnectorService,
        gitlab_sync_service: GitLabSyncService,
        repository_repository: RepositoryRepository
    ):
        self.connector_service = connector_service
        self.gitlab_sync_service = gitlab_sync_service
        self.repository_repository = repository_repository

    async def execute(self, request: SyncRepositoryRequest, user_id: int) -> Dict[str, Any]:
        """
        Execute repository sync use case.

        Args:
            request: Sync repository request
            user_id: User ID performing the sync

        Returns:
            Sync result with statistics

        Raises:
            ValueError: If validation fails
            RuntimeError: If sync operation fails
        """
        try:
            sync_result = await self.gitlab_sync_service.sync_repository_full(
                user_id=user_id,
                connector_id=request.connector_id,
                repository_external_id=request.project_id,
                chatbot_id=request.chatbot_id,
                branch=request.branch,
                auto_sync=request.auto_sync
            )
            return sync_result
        
        except Exception as e:
            logger.error(f"Repository sync failed: {str(e)}")
            raise RuntimeError(f"Repository sync failed: {str(e)}")


class TestGitLabConnectionUseCase:
    """
    Use case for testing GitLab connectivity.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, connector_id: int) -> Dict[str, Any]:
        """
        Execute GitLab connection test use case.

        Args:
            connector_id: GitLab connector ID to test

        Returns:
            Test result with connection status and details

        Raises:
            ResourceNotFoundError: If connector not found
            BusinessRuleViolationError: If connector not active or not a GitLab connector
        """
        # Get specific GitLab connector by ID
        gitlab_connector = self.connector_service.get_connector_by_id(connector_id)
        if not gitlab_connector:
            raise ResourceNotFoundError("GitLab connector", str(connector_id))

        if not gitlab_connector.is_active:
            raise BusinessRuleViolationError(
                f"GitLab connector with ID {connector_id} is not active",
                "CONNECTOR_NOT_ACTIVE"
            )

        if gitlab_connector.provider_type != "gitlab":
            raise BusinessRuleViolationError(
                f"Connector {connector_id} is not a GitLab connector",
                "INVALID_CONNECTOR_TYPE"
            )

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
                    "connector_id": gitlab_connector.id,
                    "id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "name": user_info.get("name"),
                    "email": user_info.get("email")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"GitLab connection failed: {str(e)}",
                "details": {"error": str(e)}
            }


class FetchGitLabRepositoriesUseCase:
    """
    Use case for fetching repositories from GitLab.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, connector_id: int) -> Dict[str, Any]:
        """
        Execute fetch GitLab repositories use case.

        Args:
            connector_id: GitLab connector ID to use for fetching repositories
            per_page: Number of repositories per page
            page: Page number to fetch

        Returns:
            Repository list with pagination info
        """
        try:
            # Get specific GitLab connector by ID
            gitlab_connector = self.connector_service.get_connector_by_id(connector_id)
            if not gitlab_connector or not gitlab_connector.is_active:
                raise ValueError(f"GitLab connector with ID {connector_id} not found or not active")

            if gitlab_connector.provider_type != "gitlab":
                raise ValueError(f"Connector {connector_id} is not a GitLab connector")

            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

            # Fetch all repositories without pagination
            repositories = gitlab_service.get_projects()

            return {
                "success": True,
                **repositories
            }

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise ValueError(f"Failed to fetch repositories: {e}")


class FetchGitLabBranchesUseCase:
    """
    Use case for fetching branches from a GitLab project.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, connector_id: int, project_id: int) -> Dict[str, Any]:
        """
        Execute fetch GitLab branches use case.

        Args:
            connector_id: GitLab connector ID to use
            project_id: GitLab project ID (numeric ID from GitLab API)

        Returns:
            Branch list with project information

        Raises:
            ResourceNotFoundError: If connector not found
            BusinessRuleViolationError: If connector not active or not GitLab
        """
        # Get specific GitLab connector by ID
        gitlab_connector = self.connector_service.get_connector_by_id(connector_id)
        if not gitlab_connector:
            raise ResourceNotFoundError("GitLab connector", str(connector_id))

        if not gitlab_connector.is_active:
            raise BusinessRuleViolationError(
                f"GitLab connector with ID {connector_id} is not active",
                "CONNECTOR_NOT_ACTIVE"
            )

        if gitlab_connector.provider_type != "gitlab":
            raise BusinessRuleViolationError(
                f"Connector {connector_id} is not a GitLab connector",
                "INVALID_CONNECTOR_TYPE"
            )

        try:
            # Get GitLab service
            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)

            # Get branches directly using project_id
            branches = gitlab_service.get_branches(project_id)

            return {
                "branches": branches  # Returns only the list of branch names
            }

        except Exception as e:
            logger.error(f"Failed to fetch GitLab branches: {e}")
            raise ValueError(f"Failed to fetch GitLab branches: {str(e)}")
