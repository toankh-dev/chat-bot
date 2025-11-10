"""
Conversation use cases.

Defines application-level use cases for conversation operations.
"""

from typing import List, Dict, Any
from application.services.conversation_service import ConversationService
from shared.interfaces.services.ai_services.rag_service import IRAGService
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository
from schemas.conversation_schema import (
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
    Use case for creating message in conversation with RAG-powered AI response.

    This use case:
    1. Saves the user's message
    2. Retrieves chatbot configuration
    3. Uses RAG to generate AI response based on knowledge base
    4. Saves AI response
    5. Returns the AI response
    """

    def __init__(
        self,
        conversation_service: ConversationService,
        rag_service: IRAGService,
        chatbot_repository: ChatbotRepository,
        domain: str = "general"  # Default domain, can be overridden
    ):
        self.conversation_service = conversation_service
        self.rag_service = rag_service
        self.chatbot_repository = chatbot_repository
        self.domain = domain

    async def execute(
        self,
        conversation_id: int,
        request: MessageCreate,
        user_id: int
    ) -> MessageResponse:
        """
        Execute create message use case with RAG-powered AI response.

        Args:
            conversation_id: Conversation ID
            request: Message creation data
            user_id: User ID for ownership verification

        Returns:
            MessageResponse: AI response message (user message is saved but not returned)
        """
        # 1. Save user message
        user_message = await self.conversation_service.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=request.content,
            role="user"
        )

        # 2. Get conversation with chatbot info
        conversation = await self.conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=user_id
        )

        # 3. Get chatbot configuration
        chatbot = await self.chatbot_repository.find_by_id(conversation.chatbot_id)
        if not chatbot:
            raise ValueError(f"Chatbot {conversation.chatbot_id} not found")

        # 4. Get conversation history for context (last N messages)
        history_context = ""
        if hasattr(conversation, 'messages') and conversation.messages:
            # Get last 10 messages for context
            recent_messages = conversation.messages[-10:]
            history_context = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in recent_messages
            ])

        # 5. Use RAG to generate AI response
        try:
            # Build enhanced query with system prompt and history
            enhanced_query = f"{request.content}"
            if history_context:
                enhanced_query = f"Conversation history:\n{history_context}\n\nUser question: {request.content}"

            rag_result = await self.rag_service.retrieve_and_generate(
                query=enhanced_query,
                domain=self.domain,
                max_results=5
            )

            ai_response_content = rag_result.get("answer", "I couldn't generate a response at this time.")

            # Store RAG metadata
            metadata = {
                "rag_used": True,
                "contexts_count": len(rag_result.get("contexts", [])),
                "domain": self.domain
            }

        except Exception as e:
            # Fallback to simple response if RAG fails
            ai_response_content = chatbot.fallback_message or "I'm having trouble accessing my knowledge base right now."
            metadata = {
                "rag_used": False,
                "error": str(e)
            }

        # 6. Save AI response
        ai_message = await self.conversation_service.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=ai_response_content,
            role="assistant",
            metadata=metadata
        )

        return MessageResponse.model_validate(ai_message)


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
