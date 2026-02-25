"""
KnowledgeBaseSource domain entity.

Represents a data source linked to a knowledge base.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class KnowledgeBaseSourceEntity:
    """
    Knowledge Base Source entity.

    Links a data source (repository, document, API) to a knowledge base.
    Uses polymorphic pattern: source_type + source_id to reference different sources.
    """

    id: Optional[int]
    knowledge_base_id: int
    source_type: str  # 'repository', 'document', 'api', 'external'
    source_id: str  # ID of the source (repo.id, doc.id, etc)
    config: Optional[dict]  # include/exclude patterns, filters, etc
    auto_sync: bool = False
    sync_status: Optional[str] = None  # pending, syncing, completed, failed
    last_synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Valid source types
    SOURCE_TYPE_REPOSITORY = "repository"
    SOURCE_TYPE_DOCUMENT = "document"
    SOURCE_TYPE_API = "api"
    SOURCE_TYPE_EXTERNAL = "external"

    VALID_SOURCE_TYPES = [
        SOURCE_TYPE_REPOSITORY,
        SOURCE_TYPE_DOCUMENT,
        SOURCE_TYPE_API,
        SOURCE_TYPE_EXTERNAL,
    ]

    # Valid sync statuses
    SYNC_STATUS_PENDING = "pending"
    SYNC_STATUS_SYNCING = "syncing"
    SYNC_STATUS_COMPLETED = "completed"
    SYNC_STATUS_FAILED = "failed"

    VALID_SYNC_STATUSES = [
        SYNC_STATUS_PENDING,
        SYNC_STATUS_SYNCING,
        SYNC_STATUS_COMPLETED,
        SYNC_STATUS_FAILED,
    ]

    def __post_init__(self):
        """Validate source data."""
        if self.knowledge_base_id <= 0:
            raise ValueError("Knowledge base ID must be a positive integer")

        if not self.source_type or self.source_type not in self.VALID_SOURCE_TYPES:
            raise ValueError(
                f"Source type must be one of: {', '.join(self.VALID_SOURCE_TYPES)}"
            )

        if not self.source_id or not self.source_id.strip():
            raise ValueError("Source ID cannot be empty")

        if self.sync_status and self.sync_status not in self.VALID_SYNC_STATUSES:
            raise ValueError(
                f"Sync status must be one of: {', '.join(self.VALID_SYNC_STATUSES)}"
            )

    @property
    def is_persisted(self) -> bool:
        """Check if source has been saved to database."""
        return self.id is not None

    def mark_syncing(self) -> None:
        """Mark source as currently syncing."""
        self.sync_status = self.SYNC_STATUS_SYNCING

    def mark_completed(self) -> None:
        """Mark source sync as completed."""
        self.sync_status = self.SYNC_STATUS_COMPLETED
        self.last_synced_at = datetime.now()

    def mark_failed(self) -> None:
        """Mark source sync as failed."""
        self.sync_status = self.SYNC_STATUS_FAILED

    def __str__(self) -> str:
        """String representation."""
        return (
            f"KnowledgeBaseSource(id={self.id}, kb_id={self.knowledge_base_id}, "
            f"type={self.source_type}, source_id={self.source_id})"
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"KnowledgeBaseSource(id={self.id}, kb_id={self.knowledge_base_id}, "
            f"type={self.source_type}, source_id={self.source_id}, "
            f"auto_sync={self.auto_sync}, status={self.sync_status})"
        )


# Backwards compatibility alias
KnowledgeBaseSource = KnowledgeBaseSourceEntity
