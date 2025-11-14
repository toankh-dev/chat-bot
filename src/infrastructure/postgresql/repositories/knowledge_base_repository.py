"""
KnowledgeBase repository implementation.

Handles database operations for knowledge bases.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.knowledge_base import KnowledgeBaseEntity
from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel
from infrastructure.postgresql.mappers.knowledge_base_mapper import KnowledgeBaseMapper


class KnowledgeBaseRepository:
    """
    Repository for KnowledgeBase CRUD operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, entity: KnowledgeBaseEntity) -> KnowledgeBaseEntity:
        """
        Create a new knowledge base.

        Args:
            entity: KnowledgeBase entity to create

        Returns:
            Created KnowledgeBase entity with ID
        """
        model = KnowledgeBaseMapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return KnowledgeBaseMapper.to_entity(model)

    async def update(self, entity: KnowledgeBaseEntity) -> KnowledgeBaseEntity:
        """
        Update an existing knowledge base.

        Args:
            entity: KnowledgeBase entity to update

        Returns:
            Updated KnowledgeBase entity

        Raises:
            ValueError: If knowledge base not found
        """
        if entity.id is None:
            raise ValueError("Cannot update knowledge base without ID")

        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == entity.id)
        result = await self.session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if not existing_model:
            raise ValueError(f"Knowledge base with ID {entity.id} not found")

        updated_model = KnowledgeBaseMapper.to_model(entity, existing_model)
        await self.session.flush()
        await self.session.refresh(updated_model)
        return KnowledgeBaseMapper.to_entity(updated_model)

    async def get_by_id(self, kb_id: int) -> Optional[KnowledgeBaseEntity]:
        """
        Get knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            KnowledgeBase entity or None if not found
        """
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return KnowledgeBaseMapper.to_entity(model) if model else None

    async def get_by_chatbot_id(self, chatbot_id: int) -> List[KnowledgeBaseEntity]:
        """
        Get all knowledge bases for a chatbot.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            List of KnowledgeBase entities
        """
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.chatbot_id == chatbot_id
        ).order_by(KnowledgeBaseModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [KnowledgeBaseMapper.to_entity(model) for model in models]

    async def get_active_by_chatbot_id(self, chatbot_id: int) -> List[KnowledgeBaseEntity]:
        """
        Get all active knowledge bases for a chatbot.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            List of active KnowledgeBase entities
        """
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.chatbot_id == chatbot_id,
            KnowledgeBaseModel.is_active == True
        ).order_by(KnowledgeBaseModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [KnowledgeBaseMapper.to_entity(model) for model in models]

    async def find_by_name_and_chatbot(
        self,
        name: str,
        chatbot_id: int
    ) -> Optional[KnowledgeBaseEntity]:
        """
        Find knowledge base by name and chatbot ID.

        Args:
            name: Knowledge base name
            chatbot_id: Chatbot ID

        Returns:
            KnowledgeBase entity or None if not found
        """
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.name == name,
            KnowledgeBaseModel.chatbot_id == chatbot_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return KnowledgeBaseMapper.to_entity(model) if model else None

    async def delete(self, kb_id: int) -> bool:
        """
        Delete knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if deleted, False if not found
        """
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True
