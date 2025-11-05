"""
Chatbot repository implementation.

Implements chatbot data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.models import Chatbot
from src.shared.repositories.base_repository import BaseRepository


class ChatbotRepositoryImpl(BaseRepository[Chatbot, int]):
    """
    Chatbot repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[Chatbot]:
        """Find chatbot by ID."""
        result = await self.session.execute(
            select(Chatbot).where(Chatbot.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """Find all chatbots with pagination."""
        result = await self.session.execute(
            select(Chatbot).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: Chatbot) -> Chatbot:
        """Create new chatbot."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: Chatbot) -> Chatbot:
        """Update existing chatbot."""
        await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete chatbot by ID."""
        chatbot = await self.find_by_id(id)
        if chatbot:
            await self.session.delete(chatbot)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if chatbot exists."""
        result = await self.session.execute(
            select(Chatbot.id).where(Chatbot.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """Find all active chatbots."""
        result = await self.session.execute(
            select(Chatbot).where(Chatbot.status == "active").offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_creator(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """Find chatbots created by specific user."""
        result = await self.session.execute(
            select(Chatbot).where(Chatbot.created_by == creator_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
