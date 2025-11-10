"""
Connector Repository - Database operations for connectors.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from infrastructure.postgresql.models.connector_model import ConnectorModel


class ConnectorRepository:
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
