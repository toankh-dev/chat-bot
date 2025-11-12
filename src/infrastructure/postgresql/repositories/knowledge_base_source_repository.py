"""
KnowledgeBaseSource repository implementation.

Handles database operations for knowledge base sources.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.knowledge_base_source import KnowledgeBaseSourceEntity
from infrastructure.postgresql.models.knowledge_base_source_model import KnowledgeBaseSourceModel
from infrastructure.postgresql.mappers.knowledge_base_source_mapper import KnowledgeBaseSourceMapper


class KnowledgeBaseSourceRepository:
    """
    Repository for KnowledgeBaseSource CRUD operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, entity: KnowledgeBaseSourceEntity) -> KnowledgeBaseSourceEntity:
        """
        Create a new knowledge base source.

        Args:
            entity: KnowledgeBaseSource entity to create

        Returns:
            Created KnowledgeBaseSource entity with ID
        """
        model = KnowledgeBaseSourceMapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return KnowledgeBaseSourceMapper.to_entity(model)

    async def update(self, entity: KnowledgeBaseSourceEntity) -> KnowledgeBaseSourceEntity:
        """
        Update an existing knowledge base source.

        Args:
            entity: KnowledgeBaseSource entity to update

        Returns:
            Updated KnowledgeBaseSource entity

        Raises:
            ValueError: If source not found
        """
        if entity.id is None:
            raise ValueError("Cannot update knowledge base source without ID")

        stmt = select(KnowledgeBaseSourceModel).where(KnowledgeBaseSourceModel.id == entity.id)
        result = await self.session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if not existing_model:
            raise ValueError(f"Knowledge base source with ID {entity.id} not found")

        updated_model = KnowledgeBaseSourceMapper.to_model(entity, existing_model)
        await self.session.flush()
        await self.session.refresh(updated_model)
        return KnowledgeBaseSourceMapper.to_entity(updated_model)

    async def get_by_id(self, source_id: int) -> Optional[KnowledgeBaseSourceEntity]:
        """
        Get knowledge base source by ID.

        Args:
            source_id: Source ID

        Returns:
            KnowledgeBaseSource entity or None if not found
        """
        stmt = select(KnowledgeBaseSourceModel).where(KnowledgeBaseSourceModel.id == source_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return KnowledgeBaseSourceMapper.to_entity(model) if model else None

    async def get_by_knowledge_base_id(self, kb_id: int) -> List[KnowledgeBaseSourceEntity]:
        """
        Get all sources for a knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            List of KnowledgeBaseSource entities
        """
        stmt = select(KnowledgeBaseSourceModel).where(
            KnowledgeBaseSourceModel.knowledge_base_id == kb_id
        ).order_by(KnowledgeBaseSourceModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [KnowledgeBaseSourceMapper.to_entity(model) for model in models]

    async def find_by_source(
        self,
        kb_id: int,
        source_type: str,
        source_id: str
    ) -> Optional[KnowledgeBaseSourceEntity]:
        """
        Find source by knowledge base, type, and source ID.

        Args:
            kb_id: Knowledge base ID
            source_type: Source type (repository, document, etc.)
            source_id: Source ID

        Returns:
            KnowledgeBaseSource entity or None if not found
        """
        stmt = select(KnowledgeBaseSourceModel).where(
            KnowledgeBaseSourceModel.knowledge_base_id == kb_id,
            KnowledgeBaseSourceModel.source_type == source_type,
            KnowledgeBaseSourceModel.source_id == source_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return KnowledgeBaseSourceMapper.to_entity(model) if model else None

    async def get_by_source_type(
        self,
        kb_id: int,
        source_type: str
    ) -> List[KnowledgeBaseSourceEntity]:
        """
        Get all sources of a specific type for a knowledge base.

        Args:
            kb_id: Knowledge base ID
            source_type: Source type (repository, document, etc.)

        Returns:
            List of KnowledgeBaseSource entities
        """
        stmt = select(KnowledgeBaseSourceModel).where(
            KnowledgeBaseSourceModel.knowledge_base_id == kb_id,
            KnowledgeBaseSourceModel.source_type == source_type
        ).order_by(KnowledgeBaseSourceModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [KnowledgeBaseSourceMapper.to_entity(model) for model in models]

    async def get_auto_sync_sources(self) -> List[KnowledgeBaseSourceEntity]:
        """
        Get all sources with auto_sync enabled.

        Returns:
            List of KnowledgeBaseSource entities with auto_sync=True
        """
        stmt = select(KnowledgeBaseSourceModel).where(
            KnowledgeBaseSourceModel.auto_sync == True
        ).order_by(KnowledgeBaseSourceModel.last_synced_at.asc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [KnowledgeBaseSourceMapper.to_entity(model) for model in models]

    async def delete(self, source_id: int) -> bool:
        """
        Delete knowledge base source by ID.

        Args:
            source_id: Source ID

        Returns:
            True if deleted, False if not found
        """
        stmt = select(KnowledgeBaseSourceModel).where(KnowledgeBaseSourceModel.id == source_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True
