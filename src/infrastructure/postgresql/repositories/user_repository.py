"""
User repository implementation.

Implements user data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.user import UserEntity
from infrastructure.postgresql.models import UserModel
from infrastructure.postgresql.mappers.user_mapper import UserMapper
from shared.interfaces.repositories.user_repository import UserRepository


class UserRepositoryImpl(UserRepository):
    """
    User repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserMapper

    async def find_by_id(self, id: int) -> Optional[UserEntity]:
        """Find user by ID and return domain entity."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        """Find all users with pagination and return domain entities."""
        result = await self.session.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(self, entity: UserEntity) -> UserEntity:
        """Create new user from domain entity."""
        model = self.mapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(self, entity: UserEntity) -> UserEntity:
        """Update existing user from domain entity."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == entity.id)
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
        """Delete user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if user exists."""
        result = await self.session.execute(
            select(UserModel.id).where(UserModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Find user by email and return domain entity."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_active_users(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        """Find all active users and return domain entities."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.status == "active").offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]
