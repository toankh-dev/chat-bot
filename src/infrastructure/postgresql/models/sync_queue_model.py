"""
SyncQueue SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from infrastructure.postgresql.connection.base import Base


class SyncQueueModel(Base):
    """Sync queue model for pending file processing."""
    __tablename__ = "sync_queue"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Repository"
    )
    commit_id = Column(
        Integer,
        ForeignKey("commits.id", ondelete="CASCADE"),
        nullable=False,
        comment="Commit that changed this file"
    )
    file_change_history_id = Column(
        Integer,
        ForeignKey("file_change_history.id", ondelete="SET NULL"),
        comment="Reference to file change history"
    )
    file_path = Column(Text, nullable=False)
    change_type = Column(String(20), nullable=False)  # added, modified, deleted, renamed
    priority = Column(Integer, default=0, comment="Higher priority processed first")

    # Status
    status = Column(
        String(20),
        default="pending",
        comment="Status: pending, processing, completed, failed"
    )
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, comment="Last error message (sanitized)")

    # Timing
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    next_retry_at = Column(DateTime, comment="When to retry with exponential backoff")

    def __repr__(self):
        return f"<SyncQueue(id={self.id}, file_path='{self.file_path}', status='{self.status}')>"
