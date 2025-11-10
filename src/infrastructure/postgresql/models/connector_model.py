"""
Connector SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from infrastructure.postgresql.connection.base import Base


class ConnectorModel(Base):
    """Connector model for third-party integrations."""
    __tablename__ = "connectors"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="Connector name (e.g., GitLab, GitHub)")
    provider_type = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Provider type (gitlab, github, jira, etc.)"
    )
    auth_type = Column(
        String(20),
        nullable=False,
        comment="Authentication type (oauth2, personal_token, api_key)"
    )
    client_id = Column(Text, nullable=True, comment="OAuth2 client ID (encrypted)")
    client_secret = Column(Text, nullable=True, comment="OAuth2 client secret (encrypted)")
    config_schema = Column(
        JSONB,
        nullable=True,
        comment="Configuration schema for this connector"
    )
    is_active = Column(Boolean, default=True, comment="Whether this connector is active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user_connections = relationship(
        "UserConnectionModel",
        back_populates="connector",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Connector(id={self.id}, name='{self.name}', provider='{self.provider_type}')>"
