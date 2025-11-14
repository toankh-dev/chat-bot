"""
Chatbot repository implementation.

Implements chatbot data access using SQLAlchemy.
"""
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.chatbot import ChatbotEntity
from infrastructure.postgresql.models import ChatbotModel
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
        # Ensure ID is an integer
        chatbot_id = int(id)

        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """Find all chatbots with pagination."""
        result = await self.session.execute(select(ChatbotModel).offset(skip).limit(limit))
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(
        self,
        entity: ChatbotEntity,
        created_by: int,
        model_id: int,
        top_p=None,
        welcome_message: str = None,
        fallback_message: str = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
    ) -> ChatbotEntity:
        """
        Create new chatbot.

        Args:
            entity: Chatbot domain entity
            created_by: User ID who created the chatbot
            model_id: AI model ID
            top_p: Top-p sampling parameter
            welcome_message: Welcome message
            fallback_message: Fallback message
            max_conversation_length: Max conversation length
            enable_function_calling: Enable function calling
        """
        if top_p is None:
            top_p = Decimal("1.0")
        model = self.mapper.to_model(
            entity,
            created_by=created_by,
            model_id=model_id,
            top_p=top_p,
            welcome_message=welcome_message,
            fallback_message=fallback_message,
            max_conversation_length=max_conversation_length,
            enable_function_calling=enable_function_calling,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(
        self,
        entity: ChatbotEntity,
        created_by: int,
        model_id: Optional[int] = None,
        top_p=None,
        welcome_message: str = None,
        fallback_message: str = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
    ) -> ChatbotEntity:
        """Update existing chatbot."""
        # Find existing model using integer ID
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == entity.id)
        )
        existing_model = result.scalar_one_or_none()

        if existing_model:
            if top_p is None:
                top_p = Decimal("1.0")
            updated_model = self.mapper.to_model(
                entity,
                created_by=created_by,
                existing_model=existing_model,
                model_id=model_id,
                top_p=top_p,
                welcome_message=welcome_message,
                fallback_message=fallback_message,
                max_conversation_length=max_conversation_length,
                enable_function_calling=enable_function_calling,
            )
            await self.session.flush()
            await self.session.refresh(updated_model)
            return self.mapper.to_entity(updated_model)
        else:
            # Create new if doesn't exist
            return await self.create(
                entity,
                created_by,
                model_id or int(entity.model_id),
                top_p,
                welcome_message,
                fallback_message,
                max_conversation_length,
                enable_function_calling,
            )

    async def delete(self, id: int) -> bool:
        """Delete chatbot by ID."""
        chatbot_id = int(id)
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
        chatbot_id = int(id)
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

    async def find_by_workspace(
        self, workspace_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatbotEntity]:
        """
        Find chatbots in a specific workspace.

        Args:
            workspace_id: Workspace identifier (integer, using created_by as workspace for now)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of chatbot entities in the workspace
        """
        # Note: Using created_by as workspace for now - update when workspace model is ready
        result = await self.session.execute(
            select(ChatbotModel)
            .where(ChatbotModel.created_by == workspace_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]
