"""
User-Chatbot repository implementation.

Implements user-chatbot relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.user_chatbot import UserChatbot as UserChatbotEntity
from infrastructure.postgresql.models.user_chatbot import UserChatbot as UserChatbotModel
from infrastructure.postgresql.mappers.user_chatbot_mapper import UserChatbotMapper
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository


class UserChatbotRepositoryImpl(UserChatbotRepository):
    """
    User-Chatbot repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserChatbotMapper

    async def assign_chatbot_to_users(
        self, chatbot_id: int, user_ids: List[int], assigned_by: int
    ) -> None:
        """
        Assign chatbot to multiple users.

        This method replaces existing assignments with the new ones.
        """
        # First, remove all existing assignments
        await self.remove_chatbot_from_all_users(chatbot_id)

        # Then add new assignments
        if user_ids:
            for user_id in user_ids:
                entity = UserChatbotEntity(
                    user_id=user_id,
                    chatbot_id=chatbot_id,
                    assigned_by=assigned_by
                )
                model = self.mapper.to_model(entity)
                self.session.add(model)

            await self.session.flush()

    async def remove_chatbot_from_all_users(self, chatbot_id: int) -> None:
        """Remove chatbot from all users."""
        await self.session.execute(
            delete(UserChatbotModel).where(UserChatbotModel.chatbot_id == chatbot_id)
        )
        await self.session.flush()

    async def get_chatbot_users(self, chatbot_id: int) -> List[int]:
        """Get all user IDs a chatbot is assigned to."""
        result = await self.session.execute(
            select(UserChatbotModel.user_id)
            .where(UserChatbotModel.chatbot_id == chatbot_id)
            .where(UserChatbotModel.status == "active")
        )
        return list(result.scalars().all())

    async def get_user_chatbots(self, user_id: int) -> List[int]:
        """Get all chatbot IDs assigned to a user."""
        result = await self.session.execute(
            select(UserChatbotModel.chatbot_id)
            .where(UserChatbotModel.user_id == user_id)
            .where(UserChatbotModel.status == "active")
        )
        return list(result.scalars().all())
