"""
UserConnection SQLAlchemy ORM model.
"""

from typing import Optional
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from infrastructure.postgresql.connection.base import Base
from infrastructure.security.token_encryption import get_token_encryption_service


class UserConnectionModel(Base):
    """User connection to external services model."""
    __tablename__ = "user_connections"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who owns this connection"
    )
    connector_id = Column(
        Integer,
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
        comment="Connector being used"
    )
    access_token = Column(Text, nullable=True, comment="Access token (encrypted)")
    refresh_token = Column(Text, nullable=True, comment="Refresh token (encrypted) for OAuth2")
    expires_at = Column(DateTime, nullable=True, comment="Token expiration timestamp")
    connection_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional metadata (project_id, repository_id, etc.) - NO SENSITIVE DATA"
    )
    is_active = Column(Boolean, default=True, comment="Whether this connection is active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserModel", backref="connections")
    connector = relationship("ConnectorModel", back_populates="user_connections")

    def set_access_token(self, token: str) -> None:
        """
        Set access token with encryption.

        Args:
            token: Plain text access token
        """
        encryption_service = get_token_encryption_service()
        self.access_token = encryption_service.encrypt_token(token)

    def get_access_token(self) -> Optional[str]:
        """
        Get decrypted access token.

        Returns:
            Plain text access token or None
        """
        if not self.access_token:
            return None
        encryption_service = get_token_encryption_service()
        return encryption_service.decrypt_token(self.access_token)

    def set_refresh_token(self, token: str) -> None:
        """
        Set refresh token with encryption.

        Args:
            token: Plain text refresh token
        """
        encryption_service = get_token_encryption_service()
        self.refresh_token = encryption_service.encrypt_token(token)

    def get_refresh_token(self) -> Optional[str]:
        """
        Get decrypted refresh token.

        Returns:
            Plain text refresh token or None
        """
        if not self.refresh_token:
            return None
        encryption_service = get_token_encryption_service()
        return encryption_service.decrypt_token(self.refresh_token)

    def __repr__(self):
        return f"<UserConnection(id={self.id}, user_id={self.user_id}, connector_id={self.connector_id})>"
