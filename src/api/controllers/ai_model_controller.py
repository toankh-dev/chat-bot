"""AI Model management controller."""

from fastapi import Depends
from typing import List
from schemas.ai_model_schema import AiModelResponse, AiModelCreate, AiModelUpdate
from domain.entities.user import UserEntity
from api.middlewares.jwt_middleware import get_current_user, require_admin
from usecases.ai_model_use_cases import (
    ListAiModelsUseCase,
    GetAiModelUseCase,
    CreateAiModelUseCase,
    UpdateAiModelUseCase,
    DeleteAiModelUseCase
)
from core.dependencies import (
    get_list_ai_models_use_case,
    get_ai_model_use_case,
    get_create_ai_model_use_case,
    get_update_ai_model_use_case,
    get_delete_ai_model_use_case
)


async def list_ai_models(
    skip: int = 0,
    limit: int = 100,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListAiModelsUseCase = Depends(get_list_ai_models_use_case)
) -> List[AiModelResponse]:
    """
    List all AI models.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        use_case: List AI models use case instance

    Returns:
        List[AiModelResponse]: List of AI models
    """
    return await use_case.execute(skip=skip, limit=limit)


async def get_ai_model(
    model_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetAiModelUseCase = Depends(get_ai_model_use_case)
) -> AiModelResponse:
    """
    Get AI model by ID.

    Args:
        model_id: AI model ID
        current_user: Authenticated user
        use_case: Get AI model use case instance

    Returns:
        AiModelResponse: AI model data
    """
    return await use_case.execute(model_id)


async def create_ai_model(
    model_data: AiModelCreate,
    current_user: UserEntity = Depends(require_admin),
    use_case: CreateAiModelUseCase = Depends(get_create_ai_model_use_case)
) -> AiModelResponse:
    """
    Create new AI model (admin only).

    Args:
        model_data: AI model creation data
        current_user: Authenticated admin user
        use_case: Create AI model use case instance

    Returns:
        AiModelResponse: Created AI model data
    """
    return await use_case.execute(model_data)


async def update_ai_model(
    model_id: int,
    model_data: AiModelUpdate,
    current_user: UserEntity = Depends(require_admin),
    use_case: UpdateAiModelUseCase = Depends(get_update_ai_model_use_case)
) -> AiModelResponse:
    """
    Update AI model (admin only).

    Args:
        model_id: AI model ID
        model_data: AI model update data
        current_user: Authenticated admin user
        use_case: Update AI model use case instance

    Returns:
        AiModelResponse: Updated AI model data
    """
    return await use_case.execute(model_id, model_data)


async def delete_ai_model(
    model_id: int,
    current_user: UserEntity = Depends(require_admin),
    use_case: DeleteAiModelUseCase = Depends(get_delete_ai_model_use_case)
) -> None:
    """
    Delete AI model (admin only).

    Args:
        model_id: AI model ID
        current_user: Authenticated admin user
        use_case: Delete AI model use case instance
    """
    await use_case.execute(model_id)

