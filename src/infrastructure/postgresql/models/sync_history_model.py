"""
SyncHistory SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.postgresql.connection.base import Base


class SyncHistoryModel(Base):
    """Sync history model for tracking sync sessions."""
    __tablename__ = "sync_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Repository being synced"
    )
    sync_type = Column(String(20), nullable=False, comment="Type: full, incremental")
    triggered_by = Column(String(20), comment="Trigger: manual, scheduled")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="User who triggered sync"
    )
    from_commit_sha = Column(String(40), comment="Starting commit SHA")
    to_commit_sha = Column(String(40), nullable=False, comment="Ending commit SHA")

    # Stats
    files_queued = Column(Integer, default=0)
    files_processed = Column(Integer, default=0)
    files_succeeded = Column(Integer, default=0)
    files_failed = Column(Integer, default=0)
    files_skipped = Column(Integer, default=0)
    embeddings_created = Column(Integer, default=0)
    embeddings_deleted = Column(Integer, default=0)
    batches_total = Column(Integer, default=0)
    batches_completed = Column(Integer, default=0)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    parent_sync_id = Column(
        Integer,
        ForeignKey("sync_history.id", ondelete="SET NULL"),
        comment="Parent sync if this is a retry"
    )

    # Performance
    api_calls_made = Column(Integer, default=0)
    avg_file_process_time_ms = Column(Integer)

    # Status
    status = Column(
        String(20),
        nullable=False,
        comment="Status: running, completed, failed, partial, retrying"
    )
    error_message = Column(Text, comment="Sanitized error message")

    # Timing
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Relationships
    repository = relationship("RepositoryModel", backref="sync_histories")

    def __repr__(self):
        return f"<SyncHistory(id={self.id}, repo_id={self.repo_id}, status='{self.status}')>"
