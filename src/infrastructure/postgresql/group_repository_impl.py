"""
Group repository implementation.

Implements group data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.models import Group
from src.shared.repositories.group_repository import GroupRepository


class GroupRepositoryImpl(GroupRepository):
    """
    Group repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[Group]:
        """Find group by ID."""
        result = await self.session.execute(
            select(Group).where(Group.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Group]:
        """Find all groups with pagination."""
        result = await self.session.execute(
            select(Group).offset(skip).limit(limit).order_by(Group.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, entity: Group) -> Group:
        """Create new group."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: Group) -> Group:
        """Update existing group."""
        await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete group by ID."""
        group = await self.find_by_id(id)
        if group:
            await self.session.delete(group)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if group exists."""
        result = await self.session.execute(
            select(Group.id).where(Group.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_name(self, name: str) -> Optional[Group]:
        """Find group by name."""
        result = await self.session.execute(
            select(Group).where(Group.name == name)
        )
        return result.scalar_one_or_none()

    async def find_active_groups(self, skip: int = 0, limit: int = 100) -> List[Group]:
        """Find all groups."""
        return await self.find_all(skip=skip, limit=limit)
