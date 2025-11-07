"""
Group-Chatbot repository implementation.

Implements group-chatbot relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.models import GroupChatbot, Group, Chatbot
from src.shared.repositories.group_chatbot_repository import GroupChatbotRepository


class GroupChatbotRepositoryImpl(GroupChatbotRepository):
    """
    Group-Chatbot repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_chatbot_to_groups(
        self, chatbot_id: int, group_ids: List[int], assigned_by: int
    ) -> None:
        """
        Assign chatbot to multiple groups.

        This method replaces existing assignments with the new ones.
        """
        # First, remove all existing assignments
        await self.remove_chatbot_from_all_groups(chatbot_id)

        # Then add new assignments
        if group_ids:
            for group_id in group_ids:
                group_chatbot = GroupChatbot(
                    chatbot_id=chatbot_id,
                    group_id=group_id,
                    assigned_by=assigned_by,
                    status="active"
                )
                self.session.add(group_chatbot)

            await self.session.flush()

    async def remove_chatbot_from_all_groups(self, chatbot_id: int) -> None:
        """Remove chatbot from all groups."""
        await self.session.execute(
            delete(GroupChatbot).where(GroupChatbot.chatbot_id == chatbot_id)
        )
        await self.session.flush()

    async def get_chatbot_groups(self, chatbot_id: int) -> List[Group]:
        """Get all groups a chatbot is assigned to."""
        result = await self.session.execute(
            select(Group)
            .join(GroupChatbot, GroupChatbot.group_id == Group.id)
            .where(GroupChatbot.chatbot_id == chatbot_id)
            .where(GroupChatbot.status == "active")
            .order_by(Group.name)
        )
        return list(result.scalars().all())

    async def get_group_chatbots(self, group_id: int) -> List[int]:
        """Get all chatbot IDs assigned to a group."""
        result = await self.session.execute(
            select(GroupChatbot.chatbot_id)
            .where(GroupChatbot.group_id == group_id)
            .where(GroupChatbot.status == "active")
        )
        return list(result.scalars().all())
