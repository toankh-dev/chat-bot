"""
Chatbot use cases.

Defines application-level use cases for chatbot operations.
"""

from typing import List
from src.application.services.chatbot_service import ChatbotService
from src.schemas.chatbot_schema import (
    ChatbotCreate,
    ChatbotUpdate,
    ChatbotResponse
)


class ListChatbotsUseCase:
    """
    Use case for listing chatbots.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[ChatbotResponse]:
        """
        Execute list chatbots use case.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[ChatbotResponse]: List of chatbots
        """
        chatbots = await self.chatbot_service.list_active_chatbots(skip=skip, limit=limit)
        return [ChatbotResponse.model_validate(chatbot) for chatbot in chatbots]


class GetChatbotUseCase:
    """
    Use case for getting chatbot by ID.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int) -> ChatbotResponse:
        """
        Execute get chatbot use case.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            ChatbotResponse: Chatbot data
        """
        chatbot = await self.chatbot_service.get_chatbot_by_id(chatbot_id)
        return ChatbotResponse.model_validate(chatbot)


class CreateChatbotUseCase:
    """
    Use case for creating chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, request: ChatbotCreate, creator_id: int) -> ChatbotResponse:
        """
        Execute create chatbot use case.

        Args:
            request: Chatbot creation data
            creator_id: ID of user creating the chatbot

        Returns:
            ChatbotResponse: Created chatbot data
        """
        chatbot = await self.chatbot_service.create_chatbot(
            name=request.name,
            description=request.description,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            system_prompt=request.system_prompt,
            welcome_message=request.welcome_message,
            fallback_message=request.fallback_message,
            max_conversation_length=request.max_conversation_length,
            enable_function_calling=request.enable_function_calling,
            api_key_encrypted=request.api_key_encrypted,
            api_base_url=request.api_base_url,
            created_by=creator_id
        )
        return ChatbotResponse.model_validate(chatbot)


class UpdateChatbotUseCase:
    """
    Use case for updating chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int, request: ChatbotUpdate) -> ChatbotResponse:
        """
        Execute update chatbot use case.

        Args:
            chatbot_id: Chatbot ID
            request: Chatbot update data

        Returns:
            ChatbotResponse: Updated chatbot data
        """
        chatbot = await self.chatbot_service.update_chatbot(
            chatbot_id=chatbot_id,
            name=request.name,
            description=request.description,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            system_prompt=request.system_prompt,
            welcome_message=request.welcome_message,
            fallback_message=request.fallback_message,
            max_conversation_length=request.max_conversation_length,
            enable_function_calling=request.enable_function_calling,
            status=request.status
        )
        return ChatbotResponse.model_validate(chatbot)


class DeleteChatbotUseCase:
    """
    Use case for deleting chatbot.
    """

    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    async def execute(self, chatbot_id: int) -> bool:
        """
        Execute delete chatbot use case.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            bool: True if deleted
        """
        return await self.chatbot_service.delete_chatbot(chatbot_id)
