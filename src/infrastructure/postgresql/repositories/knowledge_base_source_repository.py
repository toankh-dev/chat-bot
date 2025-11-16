"""
KnowledgeBaseSource Sync Repository - Database operations for KB source management (SYNC).
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from infrastructure.postgresql.models.knowledge_base_source_model import (
    KnowledgeBaseSourceModel,
)
from domain.entities.knowledge_base_source import KnowledgeBaseSourceEntity
from infrastructure.postgresql.mappers.knowledge_base_source_mapper import KnowledgeBaseSourceMapper
from shared.interfaces.repositories.knowledge_base_source_repository import IKnowledgeBaseSourceRepository


class KnowledgeBaseSourceRepository(IKnowledgeBaseSourceRepository):
    """Repository for managing knowledge base source records (SYNC version for GitLab)."""

    def __init__(self, db_session: Session):
        """
        Initialize knowledge base source repository.

        Args:
            db_session: SQLAlchemy database session (sync)
        """
        self.db_session = db_session
        self.mapper = KnowledgeBaseSourceMapper

    def get_by_kb_and_source(
        self, kb_id: int, source_type: str, source_id: str
    ) -> Optional[KnowledgeBaseSourceModel]:
        """
        Get knowledge base source by KB ID, source type, and source ID.

        Args:
            kb_id: Knowledge base ID
            source_type: Source type (e.g., 'repository')
            source_id: Source identifier

        Returns:
            KnowledgeBaseSource model or None
        """
        return self.db_session.query(KnowledgeBaseSourceModel).filter(
            and_(
                KnowledgeBaseSourceModel.knowledge_base_id == kb_id,
                KnowledgeBaseSourceModel.source_type == source_type,
                KnowledgeBaseSourceModel.source_id == source_id
            )
        ).first()

    def create(self, source_data: dict) -> KnowledgeBaseSourceModel:
        """
        Create a new knowledge base source.

        Args:
            source_data: Dictionary with source fields

        Returns:
            Created KnowledgeBaseSource model
        """
        source = KnowledgeBaseSourceModel(**source_data)
        self.db_session.add(source)
        self.db_session.flush()
        self.db_session.refresh(source)
        return source

    def update(self, entity: KnowledgeBaseSourceModel) -> KnowledgeBaseSourceEntity:
        """Update existing Knowledge Base Source from domain entity."""
        # Find existing model by integer ID
        result = self.db_session.execute(
            select(KnowledgeBaseSourceModel).where(KnowledgeBaseSourceModel.id == entity.id)
        )
        existing_model = result.scalar_one_or_none()

        if existing_model:
            updated_model = self.mapper.to_model(entity, existing_model)
            self.db_session.flush()
            self.db_session.refresh(updated_model)
            return self.mapper.to_entity(updated_model)
        else:
            # Create new if doesn't exist
            return self.create(entity)
        
    def update_source_sync_status(self, source: KnowledgeBaseSourceModel) -> KnowledgeBaseSourceModel:
        """Update existing Knowledge Base Source from domain entity."""
        self.db_session.flush()
        self.db_session.refresh(source)
        return source
