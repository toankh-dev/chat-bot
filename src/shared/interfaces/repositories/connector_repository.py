"""Connector Repository Interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Any

class IConnectorRepository(ABC):
    """Interface for connector repository operations."""

    @abstractmethod
    def create(self, connector: Any) -> Any:
        """
        Create a new connector.

        Args:
            connector: Connector model instance

        Returns:
            Created connector

        Raises:
            IntegrityError: If connector with same provider_type already exists
        """
        pass

    @abstractmethod
    def get_by_id(self, connector_id: int) -> Optional[Any]:
        """
        Get connector by ID.

        Args:
            connector_id: Connector ID

        Returns:
            Connector model or None
        """
        pass

    @abstractmethod
    def get_by_provider_type(self, provider_type: str) -> Optional[Any]:
        """
        Get connector by provider type.

        Args:
            provider_type: Provider type (gitlab, github, bitbucket, etc.)

        Returns:
            Connector model or None
        """
        pass

    @abstractmethod
    def list_connector_by_user(self, user_id: int, is_active: bool = True) -> List[Any]:
        """
        List connectors that user has connections to.

        Args:
            user_id: User ID to filter by
            is_active: If True, return only active connectors and connections

        Returns:
            List of connector models that user has connections to
        """
        pass

    @abstractmethod
    def update(self, connector: Any) -> Any:
        """
        Update connector.

        Args:
            connector: Connector model with updates

        Returns:
            Updated connector
        """
        pass

    @abstractmethod
    def delete(self, connector_id: int) -> bool:
        """
        Delete connector.

        Args:
            connector_id: Connector ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def activate(self, connector_id: int) -> Optional[Any]:
        """
        Activate a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Updated connector or None
        """
        pass

    @abstractmethod
    def deactivate(self, connector_id: int) -> Optional[Any]:
        """
        Deactivate a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Updated connector or None
        """
        pass

    @abstractmethod
    def update_connector(
        self,
        connector: Any,
        name: Optional[str] = None,
        client_id: Optional[str] = None,
        config_schema: Optional[dict] = None,
        is_active: Optional[bool] = None
    ) -> Any:
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
    ) -> Any:
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