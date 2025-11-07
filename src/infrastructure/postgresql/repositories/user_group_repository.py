"""
User-Group repository implementation.

Implements user-group relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.user_group import UserGroup as UserGroupEntity
from domain.entities.group import Group as GroupEntity
from infrastructure.postgresql.models.user_group_model import UserGroup as UserGroupModel
from infrastructure.postgresql.models.group_model import Group as GroupModel
from infrastructure.postgresql.mappers.user_group_mapper import UserGroupMapper
from infrastructure.postgresql.mappers.group_mapper import GroupMapper
from shared.interfaces.repositories.user_group_repository import UserGroupRepository


class UserGroupRepositoryImpl(UserGroupRepository):
    """
    User-Group repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_group_mapper = UserGroupMapper
        self.group_mapper = GroupMapper

    async def assign_user_to_groups(
        self, user_id: int, group_ids: List[int], added_by: int
    ) -> None:
        """
        Assign user to multiple groups.

        This method replaces existing assignments with the new ones.
        """
        # First, remove all existing assignments
        await self.remove_user_from_all_groups(user_id)

        # Then add new assignments
        if group_ids:
            for group_id in group_ids:
                entity = UserGroupEntity(
                    user_id=user_id,
                    group_id=group_id,
                    added_by=added_by
                )
                model = self.user_group_mapper.to_model(entity)
                self.session.add(model)

            await self.session.flush()

    async def remove_user_from_all_groups(self, user_id: int) -> None:
        """Remove user from all groups."""
        await self.session.execute(
            delete(UserGroupModel).where(UserGroupModel.user_id == user_id)
        )
        await self.session.flush()

    async def get_user_groups(self, user_id: int) -> List[GroupEntity]:
        """Get all groups a user belongs to, returning domain entities."""
        result = await self.session.execute(
            select(GroupModel)
            .join(UserGroupModel, UserGroupModel.group_id == GroupModel.id)
            .where(UserGroupModel.user_id == user_id)
            .order_by(GroupModel.name)
        )
        models = result.scalars().all()
        return [self.group_mapper.to_entity(model) for model in models]

    async def get_group_users(self, group_id: int) -> List[int]:
        """Get all user IDs in a group."""
        result = await self.session.execute(
            select(UserGroupModel.user_id).where(UserGroupModel.group_id == group_id)
        )
        return list(result.scalars().all())
