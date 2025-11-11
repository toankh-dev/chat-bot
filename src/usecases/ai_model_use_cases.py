"""
AI Model use cases.

Defines application-level use cases for AI model operations.
"""

from typing import List
from application.services.ai_model_service import AiModelService
from schemas.ai_model_schema import (
    AiModelCreate,
    AiModelUpdate,
    AiModelResponse
)


class ListAiModelsUseCase:
    """
    Use case for listing AI models.
    """

    def __init__(self, ai_model_service: AiModelService):
        self.ai_model_service = ai_model_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[AiModelResponse]:
        """
        Execute list AI models use case.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[AiModelResponse]: List of AI models
        """
        models = await self.ai_model_service.list_ai_models(skip=skip, limit=limit)

        responses = []
        for model in models:
            model_dict = {
                "id": model.id,
                "name": model.name,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            }
            responses.append(AiModelResponse.model_validate(model_dict))

        return responses


class GetAiModelUseCase:
    """
    Use case for getting AI model by ID.
    """

    def __init__(self, ai_model_service: AiModelService):
        self.ai_model_service = ai_model_service

    async def execute(self, model_id: int) -> AiModelResponse:
        """
        Execute get AI model use case.

        Args:
            model_id: AI model ID

        Returns:
            AiModelResponse: AI model data
        """
        model = await self.ai_model_service.get_ai_model_by_id(model_id)

        model_dict = {
            "id": model.id,
            "name": model.name,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        return AiModelResponse.model_validate(model_dict)


class CreateAiModelUseCase:
    """
    Use case for creating AI model.
    """

    def __init__(self, ai_model_service: AiModelService):
        self.ai_model_service = ai_model_service

    async def execute(self, request: AiModelCreate) -> AiModelResponse:
        """
        Execute create AI model use case.

        Args:
            request: AI model creation data

        Returns:
            AiModelResponse: Created AI model data
        """
        model = await self.ai_model_service.create_ai_model(name=request.name)

        model_dict = {
            "id": model.id,
            "name": model.name,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        return AiModelResponse.model_validate(model_dict)


class UpdateAiModelUseCase:
    """
    Use case for updating AI model.
    """

    def __init__(self, ai_model_service: AiModelService):
        self.ai_model_service = ai_model_service

    async def execute(self, model_id: int, request: AiModelUpdate) -> AiModelResponse:
        """
        Execute update AI model use case.

        Args:
            model_id: AI model ID
            request: AI model update data

        Returns:
            AiModelResponse: Updated AI model data
        """
        model = await self.ai_model_service.update_ai_model(
            model_id=model_id,
            name=request.name
        )

        model_dict = {
            "id": model.id,
            "name": model.name,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        return AiModelResponse.model_validate(model_dict)


class DeleteAiModelUseCase:
    """
    Use case for deleting AI model.
    """

    def __init__(self, ai_model_service: AiModelService):
        self.ai_model_service = ai_model_service

    async def execute(self, model_id: int) -> bool:
        """
        Execute delete AI model use case.

        Args:
            model_id: AI model ID

        Returns:
            bool: True if deleted
        """
        return await self.ai_model_service.delete_ai_model(model_id)

