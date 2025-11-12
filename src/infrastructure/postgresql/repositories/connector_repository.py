"""
Connector Repository - Database operations for connectors.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from shared.interfaces.repositories.connector_repository import IConnectorRepository
from infrastructure.postgresql.models.connector_model import ConnectorModel
from core.logger import logger


class ConnectorRepository(IConnectorRepository):
    """Repository for managing connector records."""

    def __init__(self, db_session: Session):
        """
        Initialize connector repository.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

    def create(self, connector: ConnectorModel) -> ConnectorModel:
        """
        Create a new connector.

        Args:
            connector: Connector model instance

        Returns:
            Created connector

        Raises:
            IntegrityError: If connector with same provider_type already exists
        """
        self.db_session.add(connector)
        self.db_session.commit()
        self.db_session.refresh(connector)
        return connector

    def get_by_id(self, connector_id: int) -> Optional[ConnectorModel]:
        """
        Get connector by ID.

        Args:
            connector_id: Connector ID

        Returns:
            Connector model or None
        """
        return self.db_session.query(ConnectorModel).filter(
            ConnectorModel.id == connector_id
        ).first()

    def get_by_provider_type(self, provider_type: str) -> Optional[ConnectorModel]:
        """
        Get connector by provider type.

        Args:
            provider_type: Provider type (gitlab, github, bitbucket, etc.)

        Returns:
            Connector model or None
        """
        return self.db_session.query(ConnectorModel).filter(
            ConnectorModel.provider_type == provider_type
        ).first()

    def list_all(self, only_active: bool = True) -> List[ConnectorModel]:
        """
        List all connectors.

        Args:
            only_active: If True, return only active connectors

        Returns:
            List of connector models
        """
        query = self.db_session.query(ConnectorModel)

        if only_active:
            query = query.filter(ConnectorModel.is_active == True)

        return query.order_by(ConnectorModel.name).all()

    def update(self, connector: ConnectorModel) -> ConnectorModel:
        """
        Update connector.

        Args:
            connector: Connector model with updates

        Returns:
            Updated connector
        """
        self.db_session.commit()
        self.db_session.refresh(connector)
        return connector

    def delete(self, connector_id: int) -> bool:
        """
        Delete connector.

        Args:
            connector_id: Connector ID

        Returns:
            True if deleted, False if not found
        """
        connector = self.get_by_id(connector_id)
        if not connector:
            return False

        self.db_session.delete(connector)
        self.db_session.commit()
        return True

    def activate(self, connector_id: int) -> Optional[ConnectorModel]:
        """
        Activate a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Updated connector or None
        """
        connector = self.get_by_id(connector_id)
        if not connector:
            return None

        connector.is_active = True
        return self.update(connector)

    def deactivate(self, connector_id: int) -> Optional[ConnectorModel]:
        """
        Deactivate a connector.

        Args:
            connector_id: Connector ID

        Returns:
            Updated connector or None
        """
        connector = self.get_by_id(connector_id)
        if not connector:
            return None

        connector.is_active = False
        return self.update(connector)

    def update_connector(
        self,
        connector: ConnectorModel,
        name: Optional[str] = None,
        client_id: Optional[str] = None,
        config_schema: Optional[dict] = None,
        is_active: Optional[bool] = None
    ) -> ConnectorModel:
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
        from datetime import datetime
        
        if name is not None:
            connector.name = name
        if client_id is not None:
            connector.client_id = client_id
        if config_schema is not None:
            connector.config_schema = config_schema
        if is_active is not None:
            connector.is_active = is_active
        
        connector.updated_at = datetime.utcnow()
        return self.update(connector)

    def create_connector(
        self,
        name: str,
        provider_type: str,
        auth_type: str,
        client_id: Optional[str] = None,
        config_schema: Optional[dict] = None,
        is_active: bool = True
    ) -> ConnectorModel:
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
        connector = ConnectorModel(
            name=name,
            provider_type=provider_type,
            auth_type=auth_type,
            client_id=client_id,
            client_secret=None,
            config_schema=config_schema or {},
            is_active=is_active
        )
        return self.create(connector)

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
