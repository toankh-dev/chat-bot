from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.user import UserEntity
from infrastructure.postgresql.models import UserModel
from infrastructure.postgresql.mappers.user_mapper import UserMapper
from shared.interfaces.repositories.user_repository import UserRepository


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserMapper

    async def find_by_id(self, id: str) -> Optional[UserEntity]:
        try:
            user_id = int(id)
        except (ValueError, TypeError):
            return None

        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        result = await self.session.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(self, entity: UserEntity) -> UserEntity:
        model = self.mapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(self, entity: UserEntity) -> UserEntity:
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
            return await self.create(entity)

    async def delete(self, id: str) -> bool:
        try:
            user_id = int(id)
        except (ValueError, TypeError):
            return False
            
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: str) -> bool:
        try:
            user_id = int(id)
        except (ValueError, TypeError):
            return False

        result = await self.session.execute(
            select(UserModel.id).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_active_users(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.status == "active").offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def find_first_admin(self) -> Optional[UserEntity]:
        result = await self.session.execute(
            select(UserModel)
            .where(UserModel.is_admin == True)
            .order_by(UserModel.id.asc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def count_active_admins(self, exclude_user_id: Optional[int] = None) -> int:
        query = select(func.count(UserModel.id)).where(
            UserModel.is_admin == True,
            UserModel.status == 'active'
        )
        if exclude_user_id is not None:
            query = query.where(UserModel.id != exclude_user_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
