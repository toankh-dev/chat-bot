"""
KnowledgeBase Sync Repository - Database operations for knowledge base management (SYNC).
"""

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel
from shared.interfaces.repositories.knowledge_base_repository import IKnowledgeBaseRepository


class KnowledgeBaseRepository(IKnowledgeBaseRepository):
    """Repository for managing knowledge base records (SYNC version for GitLab)."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize knowledge base repository.

        Args:
            db_session: SQLAlchemy database session (sync)
        """
        self.db_session = db_session

    async def get_by_chatbot_id(self, chatbot_id: int):
        stmt = select(KnowledgeBaseModel).filter_by(chatbot_id=chatbot_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def create(self, kb_data: dict) -> KnowledgeBaseModel:
        """
        Create a new knowledge base.

        Args:
            kb_data: Dictionary with KB fields (chatbot_id, name, description, etc.)

        Returns:
            Created KnowledgeBase model
        """
        kb = KnowledgeBaseModel(**kb_data)
        self.db_session.add(kb)

        await self.db_session.flush()
        await self.db_session.refresh(kb)
        return kb

    async def get_by_id(self, kb_id: int) -> Optional[KnowledgeBaseModel]:
        """
        Get knowledge base by ID.
        """
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)

        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_or_create(
        self, knowledge_base_id: Optional[int] = None, defaults: dict = None
    ) -> Tuple[KnowledgeBaseModel, bool]:

        # --- 1. Try to get existing KB ---
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_base_id)

        result = await self.db_session.execute(stmt)
        knowledge_base = result.scalars().first()

        if knowledge_base:
            return knowledge_base, False

        # --- 2. Create new KB ---
        data = defaults or {}
        knowledge_base = KnowledgeBaseModel(**data)

        self.db_session.add(knowledge_base)
        await self.db_session.flush()
        await self.db_session.refresh(knowledge_base)

        return knowledge_base, True
