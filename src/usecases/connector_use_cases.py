"""
Connector use cases for admin management.
Handles business logic for connector operations.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from application.services.connector_service import ConnectorService
from infrastructure.postgresql.models.connector_model import ConnectorModel
from schemas.connector_schema import (
    GitLabPersonalTokenSetupRequest,
    ConnectorCredentialsUpdateRequest
)

logger = logging.getLogger(__name__)


class ConnectorUseCases:
    """
    Use cases for connector management.
    Encapsulates business logic for admin connector operations.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.connector_service = ConnectorService(db_session)
    
    def list_connectors(self) -> List[ConnectorModel]:
        """
        List all configured connectors.
        
        Returns:
            List of ConnectorModel instances
        """
        try:
            return self.connector_service.list_all_connectors()
        except Exception as e:
            logger.error(f"Failed to list connectors: {e}")
            raise ValueError(f"Failed to list connectors: {e}")
    
    def get_connector_by_id(self, connector_id: int) -> ConnectorModel:
        """
        Get connector by ID.
        
        Args:
            connector_id: Connector ID to retrieve
            
        Returns:
            ConnectorModel instance
            
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
    
    def setup_gitlab_personal_token_connector(
        self, 
        request: GitLabPersonalTokenSetupRequest
    ) -> ConnectorModel:
        """
        Set up GitLab personal token connector.
        This is idempotent - it will update existing connector or create new one.

        Args:
            request: GitLab setup request with token and configuration

        Returns:
            ConnectorModel instance (with stable ID)
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

            logger.info(f"Successfully configured GitLab connector: ID={connector.id}")
            return connector
            
        except Exception as e:
            logger.error(f"Failed to setup GitLab connector: {e}")
            raise ValueError(f"Failed to setup GitLab connector: {e}")
    
    def update_connector_credentials(
        self,
        connector_id: int,
        request: ConnectorCredentialsUpdateRequest
    ) -> ConnectorModel:
        """
        Update connector credentials.
        
        Args:
            connector_id: Connector ID to update
            request: Request with new credentials
            
        Returns:
            Updated ConnectorModel instance
        """
        try:
            # Validate connector exists and is personal token type
            connector = self.get_connector_by_id(connector_id)
            if connector.auth_type != "personal_token":
                raise ValueError(f"Connector {connector_id} is not using personal token authentication")
            
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

    def delete_connector(self, connector_id: int) -> None:
        """
        Delete a connector.
        
        Args:
            connector_id: Connector ID to delete
        """
        try:
            connector = self.get_connector_by_id(connector_id)
            self.connector_service.delete_connector(connector_id)
            
            logger.info(f"Successfully deleted connector {connector_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete connector {connector_id}: {e}")
            raise ValueError(f"Failed to delete connector: {e}")