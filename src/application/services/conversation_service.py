"""
Conversation service.

Handles conversation and message management business logic.
"""

from typing import List, Optional
from datetime import datetime
from src.infrastructure.postgresql.conversation_repository_impl import (
    ConversationRepositoryImpl,
    MessageRepositoryImpl
)
from src.infrastructure.postgresql.models import Conversation, Message
from src.core.errors import NotFoundError, ValidationError, PermissionDeniedError


class ConversationService:
    """
    Service for conversation management operations.
    """

    def __init__(
        self,
        conversation_repository: ConversationRepositoryImpl,
        message_repository: MessageRepositoryImpl
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    async def get_conversation_by_id(self, conversation_id: int, user_id: int) -> Conversation:
        """
        Get conversation by ID with ownership check.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            Conversation: Found conversation

        Raises:
            NotFoundError: If conversation not found
            PermissionDeniedError: If user doesn't own the conversation
        """
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID {conversation_id} not found")

        if conversation.user_id != user_id:
            raise PermissionDeniedError("You don't have access to this conversation")

        return conversation

    async def get_conversation_with_messages(
        self,
        conversation_id: int,
        user_id: int
    ) -> Conversation:
        """
        Get conversation by ID with all messages.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            Conversation: Found conversation with messages

        Raises:
            NotFoundError: If conversation not found
            PermissionDeniedError: If user doesn't own the conversation
        """
        conversation = await self.conversation_repository.find_by_id_with_messages(conversation_id)
        if not conversation:
            raise NotFoundError(f"Conversation with ID {conversation_id} not found")

        if conversation.user_id != user_id:
            raise PermissionDeniedError("You don't have access to this conversation")

        return conversation

    async def list_user_conversations(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """
        List conversations for specific user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Conversation]: List of user's conversations
        """
        return await self.conversation_repository.find_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    async def create_conversation(
        self,
        user_id: int,
        chatbot_id: int,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create new conversation.

        Args:
            user_id: User ID
            chatbot_id: Chatbot ID
            title: Conversation title (optional)

        Returns:
            Conversation: Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            chatbot_id=chatbot_id,
            title=title or "New Conversation",
            status="active",
            is_active=True,
            message_count=0
        )

        return await self.conversation_repository.create(conversation)

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        Delete conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If conversation not found
            PermissionDeniedError: If user doesn't own the conversation
        """
        conversation = await self.get_conversation_by_id(conversation_id, user_id)
        return await self.conversation_repository.delete(conversation_id)

    async def create_message(
        self,
        conversation_id: int,
        user_id: int,
        content: str,
        role: str = "user"
    ) -> Message:
        """
        Create new message in conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership
            content: Message content
            role: Message role (user, assistant, system, tool)

        Returns:
            Message: Created message

        Raises:
            NotFoundError: If conversation not found
            PermissionDeniedError: If user doesn't own the conversation
            ValidationError: If role is invalid
        """
        conversation = await self.get_conversation_by_id(conversation_id, user_id)

        if role not in ["user", "assistant", "system", "tool"]:
            raise ValidationError(f"Invalid role: {role}")

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )

        created_message = await self.message_repository.create(message)

        # Update conversation metadata
        conversation.message_count += 1
        conversation.last_message_at = datetime.now()
        await self.conversation_repository.update(conversation)

        return created_message

    async def get_conversation_messages(
        self,
        conversation_id: int,
        user_id: int
    ) -> List[Message]:
        """
        Get all messages in a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            List[Message]: List of messages

        Raises:
            NotFoundError: If conversation not found
            PermissionDeniedError: If user doesn't own the conversation
        """
        await self.get_conversation_by_id(conversation_id, user_id)
        return await self.message_repository.find_by_conversation(conversation_id)
