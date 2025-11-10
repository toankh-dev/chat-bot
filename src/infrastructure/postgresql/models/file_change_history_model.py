"""
FileChangeHistory SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.postgresql.connection.base import Base


class FileChangeHistoryModel(Base):
    """File change history model for tracking file modifications."""
    __tablename__ = "file_change_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Repository this change belongs to"
    )
    commit_id = Column(
        Integer,
        ForeignKey("commits.id", ondelete="SET NULL"),
        comment="Commit that changed this file"
    )
    sync_history_id = Column(
        Integer,
        ForeignKey("sync_history.id", ondelete="SET NULL"),
        comment="Sync session that processed this change"
    )
    file_path = Column(Text, nullable=False, comment="Path to file in repository")
    change_type = Column(
        String(20),
        nullable=False,
        comment="Type: added, modified, deleted, renamed"
    )
    old_path = Column(Text, comment="Previous path for renamed files")

    # Stats
    additions = Column(Integer, comment="Lines added")
    deletions = Column(Integer, comment="Lines deleted")
    file_size_bytes = Column(Integer)

    # Sync tracking
    synced_at = Column(DateTime, comment="When embedding was created")
    sync_status = Column(
        String(20),
        default="pending",
        comment="Status: pending, synced, failed, skipped"
    )

    # Retry tracking
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime)
    next_retry_at = Column(DateTime, comment="When to retry (exponential backoff)")

    # Error tracking
    error_type = Column(
        String(50),
        comment="Error category: api_error, parse_error, timeout, etc."
    )
    error_message = Column(Text, comment="Sanitized error message")

    # Performance
    process_time_ms = Column(Integer, comment="Time taken to process this file")

    created_at = Column(DateTime, default=func.now())

    # Relationships
    commit = relationship("CommitModel", backref="file_changes")

    def __repr__(self):
        return f"<FileChangeHistory(id={self.id}, file_path='{self.file_path}', status='{self.sync_status}')>"
