"""
Repository SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from infrastructure.postgresql.connection.base import Base


class RepositoryModel(Base):
    """Repository model for tracking synced repositories."""
    __tablename__ = "repositories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(
        Integer,
        ForeignKey("user_connections.id", ondelete="CASCADE"),
        nullable=False,
        comment="User connection that owns this repository"
    )
    external_id = Column(
        Text,
        nullable=False,
        comment="Repository ID on external platform"
    )
    name = Column(String(255), nullable=False, comment="Repository name")
    full_name = Column(Text, nullable=True, comment="Full repository path")
    visibility = Column(String(20), nullable=True, comment="Repository visibility")
    html_url = Column(Text, nullable=True, comment="Web URL to repository")
    default_branch = Column(String(100), nullable=True, comment="Default branch name")
    repo_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional metadata"
    )
    last_synced_at = Column(
        DateTime,
        nullable=True,
        comment="Last time this repository was synced"
    )
    sync_status = Column(
        String(20),
        default="pending",
        comment="Sync status (pending, syncing, completed, failed)"
    )
    is_active = Column(Boolean, default=True, comment="Whether this repository is actively synced")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    connection = relationship("UserConnectionModel", backref="repositories")
    commits = relationship(
        "CommitModel",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.name}', full_name='{self.full_name}')>"
