"""Conversation management controller."""

from fastapi import Depends, status
from typing import List
from schemas.conversation_schema import (
    ConversationResponse,
    ConversationCreate,
    ConversationWithMessages,
    MessageCreate,
    MessageResponse
)
from domain.entities.user import UserEntity
from api.middlewares.jwt_middleware import get_current_user
from usecases.conversation_use_cases import (
    ListConversationsUseCase,
    GetConversationUseCase,
    CreateConversationUseCase,
    CreateMessageUseCase,
    DeleteConversationUseCase
)
from core.dependencies import (
    get_list_conversations_use_case,
    get_conversation_use_case,
    get_create_conversation_use_case,
    get_create_message_use_case,
    get_delete_conversation_use_case
)


async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case)
) -> List[ConversationResponse]:
    """
    List user's conversations.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        use_case: List conversations use case instance

    Returns:
        List[ConversationResponse]: List of conversations
    """
    return await use_case.execute(current_user.id, skip=skip, limit=limit)


async def get_conversation(
    conversation_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetConversationUseCase = Depends(get_conversation_use_case)
) -> ConversationWithMessages:
    """
    Get conversation with all messages.

    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        use_case: Get conversation use case instance

    Returns:
        ConversationWithMessages: Conversation with messages
    """
    return await use_case.execute(conversation_id, current_user.id)


async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: CreateConversationUseCase = Depends(get_create_conversation_use_case)
) -> ConversationResponse:
    """
    Create new conversation.

    Args:
        conversation_data: Conversation creation data
        current_user: Authenticated user
        use_case: Create conversation use case instance

    Returns:
        ConversationResponse: Created conversation data
    """
    return await use_case.execute(conversation_data, current_user.id)


async def create_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: CreateMessageUseCase = Depends(get_create_message_use_case)
) -> MessageResponse:
    """
    Create new message in conversation.

    Args:
        conversation_id: Conversation ID
        message_data: Message creation data
        current_user: Authenticated user
        use_case: Create message use case instance

    Returns:
        MessageResponse: Created message data
    """
    return await use_case.execute(conversation_id, message_data, current_user.id)


async def delete_conversation(
    conversation_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: DeleteConversationUseCase = Depends(get_delete_conversation_use_case)
) -> None:
    """
    Delete conversation.

    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        use_case: Delete conversation use case instance
    """
    await use_case.execute(conversation_id, current_user.id)
