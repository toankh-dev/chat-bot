"""
User-Group repository implementation.

Implements user-group relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.infrastructure.postgresql.models import UserGroup, Group, User
from src.shared.repositories.user_group_repository import UserGroupRepository


class UserGroupRepositoryImpl(UserGroupRepository):
    """
    User-Group repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

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
                user_group = UserGroup(
                    user_id=user_id,
                    group_id=group_id,
                    added_by=added_by
                )
                self.session.add(user_group)

            await self.session.flush()

    async def remove_user_from_all_groups(self, user_id: int) -> None:
        """Remove user from all groups."""
        await self.session.execute(
            delete(UserGroup).where(UserGroup.user_id == user_id)
        )
        await self.session.flush()

    async def get_user_groups(self, user_id: int) -> List[Group]:
        """Get all groups a user belongs to."""
        result = await self.session.execute(
            select(Group)
            .join(UserGroup, UserGroup.group_id == Group.id)
            .where(UserGroup.user_id == user_id)
            .order_by(Group.name)
        )
        return list(result.scalars().all())

    async def get_group_users(self, group_id: int) -> List[int]:
        """Get all user IDs in a group."""
        result = await self.session.execute(
            select(UserGroup.user_id).where(UserGroup.group_id == group_id)
        )
        return list(result.scalars().all())
