"""Chatbot management controller."""

from fastapi import Depends, status
from typing import List
from schemas.chatbot_schema import ChatbotResponse, ChatbotCreate, ChatbotUpdate
from domain.entities.user import UserEntity
from api.middlewares.jwt_middleware import get_current_user, require_admin
from usecases.chatbot_use_cases import (
    ListChatbotsUseCase,
    GetChatbotUseCase,
    CreateChatbotUseCase,
    UpdateChatbotUseCase,
    DeleteChatbotUseCase
)
from core.dependencies import (
    get_list_chatbots_use_case,
    get_chatbot_use_case,
    get_create_chatbot_use_case,
    get_update_chatbot_use_case,
    get_delete_chatbot_use_case
)


async def list_chatbots(
    skip: int = 0,
    limit: int = 100,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListChatbotsUseCase = Depends(get_list_chatbots_use_case)
) -> List[ChatbotResponse]:
    """
    List chatbots accessible to current user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        use_case: List chatbots use case instance

    Returns:
        List[ChatbotResponse]: List of chatbots
    """
    return await use_case.execute(skip=skip, limit=limit)


async def get_chatbot(
    chatbot_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetChatbotUseCase = Depends(get_chatbot_use_case)
) -> ChatbotResponse:
    """
    Get chatbot by ID.

    Args:
        chatbot_id: Chatbot ID
        current_user: Authenticated user
        use_case: Get chatbot use case instance

    Returns:
        ChatbotResponse: Chatbot data
    """
    return await use_case.execute(chatbot_id)


async def create_chatbot(
    chatbot_data: ChatbotCreate,
    current_user: UserEntity = Depends(require_admin),
    use_case: CreateChatbotUseCase = Depends(get_create_chatbot_use_case)
) -> ChatbotResponse:
    """
    Create new chatbot (admin only).

    Args:
        chatbot_data: Chatbot creation data
        current_user: Authenticated admin user
        use_case: Create chatbot use case instance

    Returns:
        ChatbotResponse: Created chatbot data
    """
    return await use_case.execute(chatbot_data, current_user.id)


async def update_chatbot(
    chatbot_id: int,
    chatbot_data: ChatbotUpdate,
    current_user: UserEntity = Depends(require_admin),
    use_case: UpdateChatbotUseCase = Depends(get_update_chatbot_use_case)
) -> ChatbotResponse:
    """
    Update chatbot (admin only).

    Args:
        chatbot_id: Chatbot ID
        chatbot_data: Chatbot update data
        current_user: Authenticated admin user
        use_case: Update chatbot use case instance

    Returns:
        ChatbotResponse: Updated chatbot data
    """
    return await use_case.execute(chatbot_id, chatbot_data, current_user.id)


async def delete_chatbot(
    chatbot_id: int,
    current_user: UserEntity = Depends(require_admin),
    use_case: DeleteChatbotUseCase = Depends(get_delete_chatbot_use_case)
) -> None:
    """
    Delete chatbot (admin only).

    Args:
        chatbot_id: Chatbot ID
        current_user: Authenticated admin user
        use_case: Delete chatbot use case instance
    """
    await use_case.execute(chatbot_id)
