"""
User repository implementation.

Implements user data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.postgresql.models import User
from src.shared.repositories.base_repository import BaseRepository


class UserRepositoryImpl(BaseRepository[User, int]):
    """
    User repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[User]:
        """Find user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all users with pagination."""
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: User) -> User:
        """Create new user."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: User) -> User:
        """Update existing user."""
        await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete user by ID."""
        user = await self.find_by_id(id)
        if user:
            await self.session.delete(user)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if user exists."""
        result = await self.session.execute(
            select(User.id).where(User.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all active users."""
        result = await self.session.execute(
            select(User).where(User.status == "active").offset(skip).limit(limit)
        )
        return list(result.scalars().all())
