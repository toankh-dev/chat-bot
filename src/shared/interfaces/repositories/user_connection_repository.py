"""User Connection Repository Interface."""

from abc import ABC, abstractmethod
from typing import Optional, List


class IUserConnectionRepository(ABC):
    """Interface for user connection repository operations."""

    @abstractmethod
    def create(
        self,
        user_id: int,
        connector_id: int,
        external_user_id: str,
        access_token: Optional[str] = None,
        **kwargs
    ) -> any:
        """
        Create a new user connection.

        Args:
            user_id: User ID
            connector_id: Connector ID
            external_user_id: External user ID
            access_token: Encrypted access token
            **kwargs: Additional fields

        Returns:
            Created user connection model
        """
        pass

    @abstractmethod
    def get_by_user_and_connector(
        self,
        user_id: int,
        connector_id: int
    ) -> Optional[any]:
        """
        Get user connection by user and connector.

        Args:
            user_id: User ID
            connector_id: Connector ID

        Returns:
            User connection model or None
        """
        pass

    @abstractmethod
    def list_by_connector(self, connector_id: int) -> List[any]:
        """
        List all connections for a connector.

        Args:
            connector_id: Connector ID

        Returns:
            List of user connection models
        """
        pass

    @abstractmethod
    def update(self, connection_id: int, **kwargs) -> Optional[any]:
        """
        Update user connection.

        Args:
            connection_id: Connection ID
            **kwargs: Fields to update

        Returns:
            Updated connection model or None
        """
        pass

    @abstractmethod
    def delete(self, connection_id: int) -> bool:
        """
        Delete user connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def delete_by_connector(self, connector_id: int) -> int:
        """
        Delete all connections for a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Number of connections deleted
        """
        pass

    @abstractmethod
    def get_system_connection(
        self,
        user_id: int,
        connector_id: int
    ) -> Optional[any]:
        """
        Get system connection for admin operations.

        Args:
            user_id: User ID
            connector_id: Connector ID

        Returns:
            System connection model or None
        """
        pass

    @abstractmethod
    def create_connection(
        self,
        user_id: int,
        connector_id: int,
        is_active: bool = True,
        connection_metadata: Optional[dict] = None,
        **kwargs
    ) -> any:
        """
        Create a connection with metadata.

        Args:
            user_id: User ID
            connector_id: Connector ID
            is_active: Whether connection is active
            connection_metadata: Connection metadata
            **kwargs: Additional fields

        Returns:
            Created connection model
        """
        pass

    @abstractmethod
    def count_active_connections(self, connector_id: int) -> int:
        """
        Count active connections for a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Number of active connections
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
