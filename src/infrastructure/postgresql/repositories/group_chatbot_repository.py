"""
Group-Chatbot repository implementation.

Implements group-chatbot relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.group_chatbot import GroupChatbotEntity
from domain.entities.group import GroupEntity
from infrastructure.postgresql.models.group_chatbot import GroupChatbotModel
from infrastructure.postgresql.models.group_model import Group as GroupModel
from infrastructure.postgresql.mappers.group_chatbot_mapper import GroupChatbotMapper
from infrastructure.postgresql.mappers.group_mapper import GroupMapper
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository


class GroupChatbotRepositoryImpl(GroupChatbotRepository):
    """
    Group-Chatbot repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.group_chatbot_mapper = GroupChatbotMapper
        self.group_mapper = GroupMapper

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
                entity = GroupChatbotEntity(
                    group_id=group_id,
                    chatbot_id=chatbot_id,
                    assigned_by=assigned_by
                )
                model = self.group_chatbot_mapper.to_model(entity)
                self.session.add(model)

            await self.session.flush()

    async def remove_chatbot_from_all_groups(self, chatbot_id: int) -> None:
        """Remove chatbot from all groups."""
        await self.session.execute(
            delete(GroupChatbotModel).where(GroupChatbotModel.chatbot_id == chatbot_id)
        )
        await self.session.flush()

    async def get_chatbot_groups(self, chatbot_id: int) -> List[GroupEntity]:
        """Get all groups a chatbot is assigned to, returning domain entities."""
        result = await self.session.execute(
            select(GroupModel)
            .join(GroupChatbotModel, GroupChatbotModel.group_id == GroupModel.id)
            .where(GroupChatbotModel.chatbot_id == chatbot_id)
            .where(GroupChatbotModel.status == "active")
            .order_by(GroupModel.name)
        )
        models = result.scalars().all()
        return [self.group_mapper.to_entity(model) for model in models]

    async def get_group_chatbots(self, group_id: int) -> List[int]:
        """Get all chatbot IDs assigned to a group."""
        result = await self.session.execute(
            select(GroupChatbotModel.chatbot_id)
            .where(GroupChatbotModel.group_id == group_id)
            .where(GroupChatbotModel.status == "active")
        )
        return list(result.scalars().all())
