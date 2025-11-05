"""
Conversation use cases.

Defines application-level use cases for conversation operations.
"""

from typing import List
from src.application.services.conversation_service import ConversationService
from src.schemas.conversation_schema import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    MessageCreate,
    MessageResponse
)


class ListConversationsUseCase:
    """
    Use case for listing user's conversations.
    """

    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationResponse]:
        """
        Execute list conversations use case.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[ConversationResponse]: List of conversations
        """
        conversations = await self.conversation_service.list_user_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        return [ConversationResponse.model_validate(conv) for conv in conversations]


class GetConversationUseCase:
    """
    Use case for getting conversation with messages.
    """

    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(
        self,
        conversation_id: int,
        user_id: int
    ) -> ConversationWithMessages:
        """
        Execute get conversation use case.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for ownership verification

        Returns:
            ConversationWithMessages: Conversation with all messages
        """
        conversation = await self.conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )
        return ConversationWithMessages.model_validate(conversation)


class CreateConversationUseCase:
    """
    Use case for creating conversation.
    """

    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(
        self,
        request: ConversationCreate,
        user_id: int
    ) -> ConversationResponse:
        """
        Execute create conversation use case.

        Args:
            request: Conversation creation data
            user_id: User ID

        Returns:
            ConversationResponse: Created conversation data
        """
        conversation = await self.conversation_service.create_conversation(
            user_id=user_id,
            chatbot_id=request.chatbot_id,
            title=request.title
        )
        return ConversationResponse.model_validate(conversation)


class CreateMessageUseCase:
    """
    Use case for creating message in conversation.
    """

    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(
        self,
        conversation_id: int,
        request: MessageCreate,
        user_id: int
    ) -> MessageResponse:
        """
        Execute create message use case.

        Args:
            conversation_id: Conversation ID
            request: Message creation data
            user_id: User ID for ownership verification

        Returns:
            MessageResponse: Created message data
        """
        message = await self.conversation_service.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=request.content,
            role="user"
        )
        return MessageResponse.model_validate(message)


class DeleteConversationUseCase:
    """
    Use case for deleting conversation.
    """

    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(self, conversation_id: int, user_id: int) -> bool:
        """
        Execute delete conversation use case.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for ownership verification

        Returns:
            bool: True if deleted
        """
        return await self.conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
