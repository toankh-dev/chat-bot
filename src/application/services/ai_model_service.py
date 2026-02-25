"""
AI Model service.

Handles AI model management business logic.
"""

from typing import List, Optional
from domain.entities.ai_model import AiModelEntity
from core.errors import NotFoundError, ValidationError
from shared.interfaces.repositories.ai_model_repository import AiModelRepository


class AiModelService:
    """
    Service for AI model management operations.
    """

    def __init__(self, ai_model_repository: AiModelRepository):
        self.ai_model_repository = ai_model_repository

    async def get_ai_model_by_id(self, model_id: int) -> AiModelEntity:
        """
        Get AI model by ID.

        Args:
            model_id: AI model ID

        Returns:
            AiModelEntity: Found AI model

        Raises:
            NotFoundError: If model not found
        """
        model = await self.ai_model_repository.find_by_id(model_id)
        if not model:
            raise NotFoundError(f"AI model with ID {model_id} not found")
        return model

    async def list_ai_models(self, skip: int = 0, limit: int = 100) -> List[AiModelEntity]:
        """
        List all AI models with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[AiModelEntity]: List of AI models
        """
        return await self.ai_model_repository.find_all(skip=skip, limit=limit)

    async def create_ai_model(self, name: str) -> AiModelEntity:
        """
        Create new AI model.

        Args:
            name: Model name

        Returns:
            AiModelEntity: Created AI model

        Raises:
            ValidationError: If model name already exists
        """
        existing_model = await self.ai_model_repository.find_by_name(name)
        if existing_model:
            raise ValidationError(f"AI model with name '{name}' already exists")

        model = AiModelEntity(name=name)
        return await self.ai_model_repository.create(model)

    async def update_ai_model(
        self,
        model_id: int,
        name: Optional[str] = None
    ) -> AiModelEntity:
        """
        Update AI model information.

        Args:
            model_id: AI model ID
            name: New name (optional)

        Returns:
            AiModelEntity: Updated AI model

        Raises:
            NotFoundError: If model not found
            ValidationError: If new name already exists
        """
        model = await self.get_ai_model_by_id(model_id)

        if name is not None and name != model.name:
            existing_model = await self.ai_model_repository.find_by_name(name)
            if existing_model:
                raise ValidationError(f"AI model with name '{name}' already exists")
            model.update_name(name)

        return await self.ai_model_repository.update(model)

    async def delete_ai_model(self, model_id: int) -> bool:
        """
        Delete AI model.

        Args:
            model_id: AI model ID

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If model not found
        """
        if not await self.ai_model_repository.exists(model_id):
            raise NotFoundError(f"AI model with ID {model_id} not found")

        return await self.ai_model_repository.delete(model_id)

