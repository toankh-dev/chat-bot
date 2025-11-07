"""
Chatbot repository implementation.

Implements chatbot data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.chatbot import Chatbot as ChatbotEntity
from infrastructure.postgresql.models import Chatbot as ChatbotModel
from infrastructure.postgresql.mappers.chatbot_mapper import ChatbotMapper
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository


class ChatbotRepositoryImpl(ChatbotRepository):
    """
    Chatbot repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = ChatbotMapper

    async def find_by_id(self, id: int) -> Optional[ChatbotEntity]:
        """Find chatbot by ID."""
        # Convert string ID to int for ORM query
        try:
            chatbot_id = int(id) if id.isdigit() else int(id.replace('-', '')[:8], 16) % 2147483647
        except:
            return None

        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """Find all chatbots with pagination."""
        result = await self.session.execute(
            select(ChatbotModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(self, entity: ChatbotEntity) -> ChatbotEntity:
        """Create new chatbot."""
        model = self.mapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(self, entity: ChatbotEntity) -> ChatbotEntity:
        """Update existing chatbot."""
        # Find existing model
        chatbot_id = int(str(entity.id).replace('-', '')[:8], 16) % 2147483647
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
        )
        existing_model = result.scalar_one_or_none()

        if existing_model:
            updated_model = self.mapper.to_model(entity, existing_model)
            await self.session.flush()
            await self.session.refresh(updated_model)
            return self.mapper.to_entity(updated_model)
        else:
            # Create new if doesn't exist
            return await self.create(entity)

    async def delete(self, id: int) -> bool:
        """Delete chatbot by ID."""
        chatbot_entity = await self.find_by_id(id)
        if chatbot_entity:
            chatbot_id = int(id) if id.isdigit() else int(id.replace('-', '')[:8], 16) % 2147483647
            result = await self.session.execute(
                select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
            )
            model = result.scalar_one_or_none()
            if model:
                await self.session.delete(model)
                await self.session.flush()
                return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if chatbot exists."""
        try:
            chatbot_id = int(id) if id.isdigit() else int(id.replace('-', '')[:8], 16) % 2147483647
        except:
            return False

        result = await self.session.execute(
            select(ChatbotModel.id).where(ChatbotModel.id == chatbot_id)
        )
        return result.scalar_one_or_none() is not None

    async def find_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """Find all active chatbots."""
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.status == "active").offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def find_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """Find chatbots in a specific workspace."""
        # Note: Using created_by as workspace for now - update when workspace model is ready
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.created_by == int(workspace_id)).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]