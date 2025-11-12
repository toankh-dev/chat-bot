"""
UserConnection Repository - Database operations for user connections.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from shared.interfaces.repositories.user_connection_repository import IUserConnectionRepository
from infrastructure.postgresql.models.user_connection_model import UserConnectionModel
from core.logger import logger


class UserConnectionRepository(IUserConnectionRepository):
    """Repository for managing user connection records."""

    def __init__(self, db_session: Session):
        """
        Initialize user connection repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def create(self, connection: UserConnectionModel) -> UserConnectionModel:
        """
        Create a new user connection.

        Args:
            connection: UserConnection model instance

        Returns:
            Created connection
        """
        self.db_session.add(connection)
        self.db_session.commit()
        self.db_session.refresh(connection)
        return connection

    def get_by_id(self, connection_id: int) -> Optional[UserConnectionModel]:
        """
        Get connection by ID.

        Args:
            connection_id: Connection ID

        Returns:
            UserConnection model or None
        """
        return self.db_session.query(UserConnectionModel).filter(
            UserConnectionModel.id == connection_id
        ).first()

    def get_user_connection(
        self,
        user_id: int,
        connector_id: int
    ) -> Optional[UserConnectionModel]:
        """
        Get user's connection for a specific connector.

        Args:
            user_id: User ID
            connector_id: Connector ID

        Returns:
            UserConnection model or None
        """
        return self.db_session.query(UserConnectionModel).filter(
            and_(
                UserConnectionModel.user_id == user_id,
                UserConnectionModel.connector_id == connector_id
            )
        ).first()

    def list_user_connections(
        self,
        user_id: int,
        only_active: bool = True
    ) -> List[UserConnectionModel]:
        """
        List all connections for a user.

        Args:
            user_id: User ID
            only_active: If True, return only active connections

        Returns:
            List of UserConnection models
        """
        query = self.db_session.query(UserConnectionModel).filter(
            UserConnectionModel.user_id == user_id
        )

        if only_active:
            query = query.filter(UserConnectionModel.is_active == True)

        return query.order_by(UserConnectionModel.created_at.desc()).all()

    def list_by_connector(
        self,
        connector_id: int,
        only_active: bool = True
    ) -> List[UserConnectionModel]:
        """
        List all connections for a specific connector.

        Args:
            connector_id: Connector ID
            only_active: If True, return only active connections

        Returns:
            List of UserConnection models
        """
        query = self.db_session.query(UserConnectionModel).filter(
            UserConnectionModel.connector_id == connector_id
        )

        if only_active:
            query = query.filter(UserConnectionModel.is_active == True)

        return query.all()

    def update(self, connection: UserConnectionModel) -> UserConnectionModel:
        """
        Update connection.

        Args:
            connection: UserConnection model with updates

        Returns:
            Updated connection
        """
        connection.updated_at = datetime.utcnow()
        self.db_session.commit()
        self.db_session.refresh(connection)
        return connection

    def delete(self, connection_id: int) -> bool:
        """
        Delete connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if deleted, False if not found
        """
        connection = self.get_by_id(connection_id)
        if not connection:
            return False

        self.db_session.delete(connection)
        self.db_session.commit()
        return True

    def deactivate(self, connection_id: int) -> Optional[UserConnectionModel]:
        """
        Deactivate a connection (soft delete).

        Args:
            connection_id: Connection ID

        Returns:
            Updated connection or None
        """
        connection = self.get_by_id(connection_id)
        if not connection:
            return None

        connection.is_active = False
        return self.update(connection)

    def activate(self, connection_id: int) -> Optional[UserConnectionModel]:
        """
        Activate a connection.

        Args:
            connection_id: Connection ID

        Returns:
            Updated connection or None
        """
        connection = self.get_by_id(connection_id)
        if not connection:
            return None

        connection.is_active = True
        return self.update(connection)

    def update_tokens(
        self,
        connection_id: int,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Optional[UserConnectionModel]:
        """
        Update connection tokens (encrypted).

        Args:
            connection_id: Connection ID
            access_token: New access token (plain text, will be encrypted)
            refresh_token: New refresh token (optional)
            expires_at: Token expiration time

        Returns:
            Updated connection or None
        """
        connection = self.get_by_id(connection_id)
        if not connection:
            return None

        # Use model's encryption methods
        connection.set_access_token(access_token)
        if refresh_token:
            connection.set_refresh_token(refresh_token)
        connection.expires_at = expires_at

        return self.update(connection)

    def get_expired_connections(self) -> List[UserConnectionModel]:
        """
        Get connections with expired tokens.

        Returns:
            List of connections with expired tokens
        """
        now = datetime.utcnow()
        return self.db_session.query(UserConnectionModel).filter(
            and_(
                UserConnectionModel.is_active == True,
                UserConnectionModel.expires_at.isnot(None),
                UserConnectionModel.expires_at < now
            )
        ).all()

    def verify_user_owns_connection(
        self,
        user_id: int,
        connection_id: int
    ) -> bool:
        """
        Verify that a user owns a connection.

        Args:
            user_id: User ID
            connection_id: Connection ID

        Returns:
            True if user owns connection, False otherwise
        """
        connection = self.get_by_id(connection_id)
        return connection is not None and connection.user_id == user_id

    def get_system_connection(
        self,
        user_id: int,
        connector_id: int
    ) -> Optional[UserConnectionModel]:
        """
        Get system connection for admin operations.

        Args:
            user_id: User ID
            connector_id: Connector ID

        Returns:
            System connection model or None
        """
        return self.db_session.query(UserConnectionModel).filter(
            and_(
                UserConnectionModel.user_id == user_id,
                UserConnectionModel.connector_id == connector_id,
                UserConnectionModel.is_active == True
            )
        ).filter(
            UserConnectionModel.connection_metadata.op('->>')('system') == 'true'
        ).first()

    def create_connection(
        self,
        user_id: int,
        connector_id: int,
        is_active: bool = True,
        connection_metadata: Optional[dict] = None,
        **kwargs
    ) -> UserConnectionModel:
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
        connection = UserConnectionModel(
            user_id=user_id,
            connector_id=connector_id,
            is_active=is_active,
            connection_metadata=connection_metadata or {},
            **kwargs
        )
        return self.create(connection)

    def delete_by_connector(self, connector_id: int) -> int:
        """
        Delete all connections for a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Number of connections deleted
        """
        deleted_count = self.db_session.query(UserConnectionModel).filter(
            UserConnectionModel.connector_id == connector_id
        ).delete(synchronize_session=False)
        self.db_session.commit()
        return deleted_count

    def count_active_connections(self, connector_id: int) -> int:
        """
        Count active connections for a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Number of active connections
        """
        return self.db_session.query(UserConnectionModel).filter(
            and_(
                UserConnectionModel.connector_id == connector_id,
                UserConnectionModel.is_active == True
            )
        ).count()

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise

    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise
