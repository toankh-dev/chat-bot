"""
User-Chatbot repository implementation.

Implements user-chatbot relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.models import UserChatbot
from src.shared.repositories.user_chatbot_repository import UserChatbotRepository


class UserChatbotRepositoryImpl(UserChatbotRepository):
    """
    User-Chatbot repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

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
                user_chatbot = UserChatbot(
                    chatbot_id=chatbot_id,
                    user_id=user_id,
                    assigned_by=assigned_by,
                    status="active"
                )
                self.session.add(user_chatbot)

            await self.session.flush()

    async def remove_chatbot_from_all_users(self, chatbot_id: int) -> None:
        """Remove chatbot from all users."""
        await self.session.execute(
            delete(UserChatbot).where(UserChatbot.chatbot_id == chatbot_id)
        )
        await self.session.flush()

    async def get_chatbot_users(self, chatbot_id: int) -> List[int]:
        """Get all user IDs a chatbot is assigned to."""
        result = await self.session.execute(
            select(UserChatbot.user_id)
            .where(UserChatbot.chatbot_id == chatbot_id)
            .where(UserChatbot.status == "active")
        )
        return list(result.scalars().all())

    async def get_user_chatbots(self, user_id: int) -> List[int]:
        """Get all chatbot IDs assigned to a user."""
        result = await self.session.execute(
            select(UserChatbot.chatbot_id)
            .where(UserChatbot.user_id == user_id)
            .where(UserChatbot.status == "active")
        )
        return list(result.scalars().all())
