"""
Commit SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from infrastructure.postgresql.connection.base import Base


class CommitModel(Base):
    """Commit model for tracking repository commits."""
    __tablename__ = "commits"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Repository this commit belongs to"
    )
    external_id = Column(Text, nullable=False, comment="Commit ID on external platform")
    sha = Column(String(40), nullable=False, comment="Git commit SHA")
    author_name = Column(String(255), nullable=True, comment="Commit author name")
    author_email = Column(String(255), nullable=True, comment="Commit author email")
    message = Column(Text, nullable=True, comment="Commit message")
    committed_at = Column(DateTime, nullable=True, comment="When the commit was made")
    files_changed = Column(Integer, nullable=True, comment="Number of files changed")
    additions = Column(Integer, nullable=True, comment="Lines added")
    deletions = Column(Integer, nullable=True, comment="Lines deleted")
    commit_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        comment="Additional commit metadata"
    )
    synced_at = Column(DateTime, nullable=True, comment="When this commit was synced to KB")
    created_at = Column(DateTime, default=func.now())

    # Relationships
    repository = relationship("RepositoryModel", back_populates="commits")

    def __repr__(self):
        return f"<Commit(id={self.id}, sha='{self.sha[:8]}', message='{self.message[:50]}')>"
