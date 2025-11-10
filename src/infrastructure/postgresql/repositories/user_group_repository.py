"""
User-Group repository implementation.

Implements user-group relationship management using SQLAlchemy.
"""

from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.user_group import UserGroupEntity
from domain.entities.group import GroupEntity
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
        # Convert UUID to int if needed
        try:
            if hasattr(user_id, 'value'):
                id_str = str(user_id.value)
            else:
                id_str = str(user_id)

            if id_str.isdigit():
                int_user_id = int(id_str)
            else:
                clean_id = id_str.replace('-', '')
                # Convert FULL hex UUID to int (matching user_mapper.py logic)
                if clean_id:
                    try:
                        int_user_id = int(clean_id, 16) % 2147483647  # Convert hex to int, keep in integer range
                    except ValueError:
                        int_user_id = int(clean_id) if clean_id.isdigit() else 0
                else:
                    int_user_id = 0
        except Exception as e:
            print(f"Error converting user_id {user_id} to int: {e}")
            int_user_id = user_id if isinstance(user_id, int) else 0

        # First, remove all existing assignments
        await self.remove_user_from_all_groups(int_user_id)

        # Then add new assignments
        if group_ids:
            for group_id in group_ids:
                entity = UserGroupEntity(
                    user_id=int_user_id,
                    group_id=group_id,
                    added_by=added_by
                )
                model = self.user_group_mapper.to_model(entity)
                self.session.add(model)

            await self.session.flush()

    async def remove_user_from_all_groups(self, user_id: int) -> None:
        """Remove user from all groups."""
        # Convert UUID to int if needed
        try:
            if hasattr(user_id, 'value'):
                id_str = str(user_id.value)
            else:
                id_str = str(user_id)

            if id_str.isdigit():
                int_user_id = int(id_str)
            else:
                clean_id = id_str.replace('-', '')
                # Convert FULL hex UUID to int (matching user_mapper.py logic)
                if clean_id:
                    try:
                        int_user_id = int(clean_id, 16) % 2147483647  # Convert hex to int, keep in integer range
                    except ValueError:
                        int_user_id = int(clean_id) if clean_id.isdigit() else 0
                else:
                    int_user_id = 0
        except Exception as e:
            print(f"Error converting user_id {user_id} to int in remove_user_from_all_groups: {e}")
            int_user_id = user_id if isinstance(user_id, int) else 0

        await self.session.execute(
            delete(UserGroupModel).where(UserGroupModel.user_id == int_user_id)
        )
        await self.session.flush()

    async def get_user_groups(self, user_id) -> List[GroupEntity]:
        """Get all groups a user belongs to, returning domain entities."""
        # Convert UUID object to int if needed - use same logic as assign_user_to_groups
        try:
            if hasattr(user_id, 'value'):
                id_str = str(user_id.value)
            else:
                id_str = str(user_id)

            if id_str.isdigit():
                int_user_id = int(id_str)
            else:
                clean_id = id_str.replace('-', '')
                # Convert FULL hex UUID to int (matching assign_user_to_groups logic)
                if clean_id:
                    try:
                        int_user_id = int(clean_id, 16) % 2147483647  # Convert hex to int, keep in integer range
                    except ValueError:
                        int_user_id = int(clean_id) if clean_id.isdigit() else 0
                else:
                    int_user_id = 0
        except Exception as e:
            print(f"Error converting user_id {user_id} to int in get_user_groups: {e}")
            int_user_id = user_id if isinstance(user_id, int) else 0

        result = await self.session.execute(
            select(GroupModel)
            .join(UserGroupModel, UserGroupModel.group_id == GroupModel.id)
            .where(UserGroupModel.user_id == int_user_id)
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
