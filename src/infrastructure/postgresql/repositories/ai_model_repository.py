"""
AI Model repository implementation.

Implements AI model data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.ai_model import AiModelEntity
from infrastructure.postgresql.models.ai_model_model import AiModelModel
from infrastructure.postgresql.mappers.ai_model_mapper import AiModelMapper
from shared.interfaces.repositories.ai_model_repository import AiModelRepository


class AiModelRepositoryImpl(AiModelRepository):
    """
    AI Model repository implementation with PostgreSQL.

    This implementation uses mappers to convert between domain entities and ORM models,
    maintaining clean separation between domain and infrastructure layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = AiModelMapper

    async def find_by_id(self, id: int) -> Optional[AiModelEntity]:
        """Find AI model by ID and return domain entity."""
        result = await self.session.execute(
            select(AiModelModel).where(AiModelModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[AiModelEntity]:
        """Find all AI models with pagination and return domain entities."""
        result = await self.session.execute(
            select(AiModelModel).offset(skip).limit(limit).order_by(AiModelModel.name.asc())
        )
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]

    async def create(self, entity: AiModelEntity) -> AiModelEntity:
        """Create new AI model from domain entity."""
        model = self.mapper.to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)

    async def update(self, entity: AiModelEntity) -> AiModelEntity:
        """Update existing AI model from domain entity."""
        # Find existing model
        result = await self.session.execute(
            select(AiModelModel).where(AiModelModel.id == entity.id)
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
        """Delete AI model by ID."""
        model_entity = await self.find_by_id(id)
        if model_entity:
            result = await self.session.execute(
                select(AiModelModel).where(AiModelModel.id == id)
            )
            model = result.scalar_one_or_none()
            if model:
                await self.session.delete(model)
                await self.session.flush()
                return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if AI model exists."""
        result = await self.session.execute(
            select(AiModelModel.id).where(AiModelModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_name(self, name: str) -> Optional[AiModelEntity]:
        """Find AI model by name and return domain entity."""
        result = await self.session.execute(
            select(AiModelModel).where(AiModelModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self.mapper.to_entity(model) if model else None

