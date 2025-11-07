"""
Group repository implementation.

Implements group data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.group import Group as GroupEntity
from infrastructure.postgresql.models.group_model import Group as GroupModel
from infrastructure.postgresql.mappers.group_mapper import GroupMapper
from shared.interfaces.repositories.group_repository import GroupRepository


class GroupRepositoryImpl(GroupRepository):
    """
    Group repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = GroupMapper

    async def find_by_id(self, id: int) -> Optional[GroupEntity]:
        """Find group by ID and return domain entity."""
        result = await self.session.execute(
            select(GroupModel).where(GroupModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[GroupEntity]:
        """Find all groups with pagination and return domain entities."""
        result = await self.session.execute(
            select(GroupModel).offset(skip).limit(limit).order_by(GroupModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(self, entity: GroupEntity) -> GroupEntity:
        """Create new group from domain entity."""
        model = self.mapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(self, entity: GroupEntity) -> GroupEntity:
        """Update existing group from domain entity."""
        # Find existing model
        result = await self.session.execute(
            select(GroupModel).where(GroupModel.id == entity.id)
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
        """Delete group by ID."""
        group_entity = await self.find_by_id(id)
        if group_entity:
            result = await self.session.execute(
                select(GroupModel).where(GroupModel.id == id)
            )
            model = result.scalar_one_or_none()
            if model:
                await self.session.delete(model)
                await self.session.flush()
                return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if group exists."""
        result = await self.session.execute(
            select(GroupModel.id).where(GroupModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_name(self, name: str) -> Optional[GroupEntity]:
        """Find group by name and return domain entity."""
        result = await self.session.execute(
            select(GroupModel).where(GroupModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_active_groups(self, skip: int = 0, limit: int = 100) -> List[GroupEntity]:
        """Find all active groups and return domain entities."""
        return await self.find_all(skip=skip, limit=limit)
