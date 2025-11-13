"""
Connector use cases for admin management.
Handles business logic for connector operations following Clean Architecture.
"""

import logging
from typing import List

from application.services.connector_service import ConnectorService
from infrastructure.postgresql.models.connector_model import ConnectorModel
from schemas.connector_schema import (
    GitLabPersonalTokenSetupRequest,
    ConnectorCredentialsUpdateRequest,
)

logger = logging.getLogger(__name__)


class ListConnectorsUseCase:
    """
    Use case for listing all connectors.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, user_id: int) -> List[ConnectorModel]:
        """
        Execute list connectors use case.

        Returns:
            List[ConnectorModel]: List of all configured connectors
        """
        try:
            return self.connector_service.list_all_connectors(user_id=user_id)
        except Exception as e:
            logger.error(f"Failed to list connectors: {e}")
            raise ValueError(f"Failed to list connectors: {e}")


class GetConnectorUseCase:
    """
    Use case for getting connector by ID.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, connector_id: int) -> ConnectorModel:
        """
        Execute get connector use case.

        Args:
            connector_id: Connector ID to retrieve

        Returns:
            ConnectorModel: Connector instance

        Raises:
            ValueError: If connector not found
        """
        try:
            connector = self.connector_service.get_connector_by_id(connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            return connector
        except Exception as e:
            logger.error(f"Failed to get connector {connector_id}: {e}")
            raise ValueError(f"Failed to get connector: {e}")


class SetupGitLabConnectorUseCase:
    """
    Use case for setting up GitLab personal token connector.
    This is idempotent - updates existing or creates new connector.
    Also creates system connection for the admin user.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    async def execute(
        self, 
        request: GitLabPersonalTokenSetupRequest, 
        admin_user_id: int
    ) -> ConnectorModel:
        """
        Execute GitLab connector setup use case.

        Args:
            request: GitLab setup request with token and configuration
            admin_user_id: Admin user ID for creating system connection

        Returns:
            ConnectorModel: Configured connector with stable ID
        """
        try:
            # Validate GitLab URL format
            if not request.gitlab_url.startswith(('http://', 'https://')):
                raise ValueError("GitLab URL must start with http:// or https://")

            # Setup connector (idempotent - updates if exists, creates if not)
            connector = self.connector_service.setup_gitlab_personal_token_connector(
                name=request.name,
                gitlab_url=request.gitlab_url,
                admin_token=request.admin_token
            )

            # Create system connection for admin user
            system_connection = await self.connector_service.get_or_create_system_connection(
                user_id=admin_user_id,
                connector=connector
            )

            logger.info(
                f"Successfully configured GitLab connector: ID={connector.id} "
                f"with system connection ID={system_connection.id}"
            )
            return connector

        except Exception as e:
            logger.error(f"Failed to setup GitLab connector: {e}")
            raise ValueError(f"Failed to setup GitLab connector: {e}")


class UpdateConnectorCredentialsUseCase:
    """
    Use case for updating connector credentials.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(
        self,
        connector_id: int,
        request: ConnectorCredentialsUpdateRequest
    ) -> ConnectorModel:
        """
        Execute update connector credentials use case.

        Args:
            connector_id: Connector ID to update
            request: Request with new credentials

        Returns:
            ConnectorModel: Updated connector instance
        """
        try:
            # Validate connector exists and is personal token type
            connector = self.connector_service.get_connector_by_id(connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")

            if connector.auth_type != "personal_token":
                raise ValueError(
                    f"Connector {connector_id} is not using personal token authentication"
                )

            # Update credentials
            updated_connector = self.connector_service.update_connector_credentials(
                connector_id=connector_id,
                personal_token=request.personal_token
            )

            logger.info(f"Successfully updated credentials for connector {connector_id}")
            return updated_connector

        except Exception as e:
            logger.error(f"Failed to update connector credentials: {e}")
            raise ValueError(f"Failed to update connector credentials: {e}")


class DeleteConnectorUseCase:
    """
    Use case for deleting a connector.
    """

    def __init__(self, connector_service: ConnectorService):
        self.connector_service = connector_service

    def execute(self, connector_id: int) -> None:
        """
        Execute delete connector use case.

        Args:
            connector_id: Connector ID to delete
        """
        try:
            # Validate connector exists
            connector = self.connector_service.get_connector_by_id(connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")

            # Delete connector
            self.connector_service.delete_connector(connector_id)

            logger.info(f"Successfully deleted connector {connector_id}")

        except Exception as e:
            logger.error(f"Failed to delete connector {connector_id}: {e}")
            raise ValueError(f"Failed to delete connector: {e}")
