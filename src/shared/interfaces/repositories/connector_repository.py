"""Connector Repository Interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime


class IConnectorRepository(ABC):
    """Interface for connector repository operations."""

    @abstractmethod
    def get_by_provider_type(self, provider_type: str) -> Optional[any]:
        """
        Get connector by provider type.

        Args:
            provider_type: Provider type (gitlab, github, etc.)

        Returns:
            Connector model or None if not found
        """
        pass

    @abstractmethod
    def get_by_id(self, connector_id: int) -> Optional[any]:
        """
        Get connector by ID.

        Args:
            connector_id: Connector ID

        Returns:
            Connector model or None if not found
        """
        pass

    @abstractmethod
    def list_all(self) -> List[any]:
        """
        List all connectors.

        Returns:
            List of all connector models
        """
        pass

    @abstractmethod
    def create(
        self,
        name: str,
        provider_type: str,
        auth_type: str,
        client_id: Optional[str],
        config_schema: dict,
        is_active: bool = True
    ) -> any:
        """
        Create a new connector.

        Args:
            name: Connector name
            provider_type: Provider type
            auth_type: Authentication type
            client_id: Encrypted client ID/token
            config_schema: Configuration schema
            is_active: Whether connector is active

        Returns:
            Created connector model
        """
        pass

    @abstractmethod
    def update(
        self,
        connector_id: int,
        **kwargs
    ) -> any:
        """
        Update an existing connector.

        Args:
            connector_id: Connector ID to update
            **kwargs: Fields to update

        Returns:
            Updated connector model
        """
        pass

    @abstractmethod
    def delete(self, connector_id: int) -> bool:
        """
        Delete a connector.

        Args:
            connector_id: Connector ID to delete

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def update_connector(
        self,
        connector: any,
        name: Optional[str] = None,
        client_id: Optional[str] = None,
        config_schema: Optional[dict] = None,
        is_active: Optional[bool] = None
    ) -> any:
        """
        Update connector fields.

        Args:
            connector: Connector model to update
            name: New name (optional)
            client_id: New client ID (optional) 
            config_schema: New config schema (optional)
            is_active: New active status (optional)

        Returns:
            Updated connector model
        """
        pass

    @abstractmethod
    def create_connector(
        self,
        name: str,
        provider_type: str,
        auth_type: str,
        client_id: Optional[str] = None,
        config_schema: Optional[dict] = None,
        is_active: bool = True
    ) -> any:
        """
        Create a new connector.

        Args:
            name: Connector name
            provider_type: Provider type
            auth_type: Authentication type
            client_id: Encrypted client ID/token
            config_schema: Configuration schema
            is_active: Whether connector is active

        Returns:
            Created connector model
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
