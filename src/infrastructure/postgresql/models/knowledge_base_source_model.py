"""
KnowledgeBaseSource SQLAlchemy model.

Represents knowledge_base_sources table in PostgreSQL.
"""

from sqlalchemy import Boolean, Column, Integer, String, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class KnowledgeBaseSourceModel(Base):
    """
    Knowledge Base Source SQLAlchemy model.

    Maps to knowledge_base_sources table.
    Polymorphic relationship to different source types (repository, document, api).
    """

    __tablename__ = "knowledge_base_sources"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)  # 'repository', 'document', 'api', 'external'
    source_id = Column(String(255), nullable=False, index=True)  # ID of the source
    config = Column(JSON, nullable=True)  # include/exclude patterns, filters
    auto_sync = Column(Boolean, nullable=False, server_default="false")
    sync_status = Column(String(50), nullable=True)  # pending, syncing, completed, failed
    last_synced_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    knowledge_base = relationship("KnowledgeBaseModel", back_populates="sources")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<KnowledgeBaseSourceModel(id={self.id}, kb_id={self.knowledge_base_id}, "
            f"type='{self.source_type}', source_id='{self.source_id}')>"
        )


# ============================================================================
# SQLALCHEMY EVENT LISTENER FOR AUTO-CLEANUP
# ============================================================================
# Automatically cleanup vectors when KB source is deleted
# ============================================================================

from sqlalchemy import event
from core.logger import logger


@event.listens_for(KnowledgeBaseSourceModel, 'before_delete')
def cleanup_vectors_before_kb_source_delete(mapper, connection, target):
    """
    Auto-cleanup vectors when KB source is deleted.

    This event fires BEFORE the DELETE but WITHIN the transaction.
    If cleanup fails, KB source is still deleted (vectors become orphaned but logged).

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: KnowledgeBaseSourceModel instance being deleted
    """
    try:
        logger.info(f"[EVENT] KB Source deletion detected: kb_source_id={target.id}")

        # Import here to avoid circular dependencies
        from core.dependencies import get_kb_cleanup_service_sync

        # Get cleanup service with sync repositories
        cleanup_service = get_kb_cleanup_service_sync()

        # Perform cleanup
        result = cleanup_service.cleanup_source_removal_sync(target.id)

        if result["success"]:
            logger.info(
                f"[EVENT] Vector cleanup successful: "
                f"kb_source_id={target.id}, deleted_vectors={result.get('deleted_vectors', 0)}"
            )
        else:
            logger.error(
                f"[EVENT] Vector cleanup failed: "
                f"kb_source_id={target.id}, error={result.get('error')}"
            )
            # Don't raise - allow KB source deletion to proceed
            # Vectors become orphaned but can be cleaned up manually

    except Exception as e:
        logger.error(
            f"[EVENT] Unexpected error in cleanup listener: "
            f"kb_source_id={target.id}, error={e}",
            exc_info=True
        )
        # Don't raise - allow KB source deletion to proceed
