"""
ChatbotEntity service.

Handles chatbot management business logic.
"""

from typing import List, Optional
from decimal import Decimal
from shared.interfaces.repositories.chatbot_repository import ChatbotRepository
from domain.entities.chatbot import Chatbot
from domain.value_objects.uuid_vo import UUID
from core.errors import NotFoundError


class ChatbotService:
    """
    Service for chatbot management operations.
    Works exclusively with domain entities, not ORM models.
    """

    def __init__(self, chatbot_repository: ChatbotRepository):
        self.chatbot_repository = chatbot_repository

    async def get_chatbot_by_id(self, chatbot_id: str) -> Chatbot:
        """
        Get chatbot by ID.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            Chatbot: Found chatbot

        Raises:
            NotFoundError: If chatbot not found
        """
        chatbot = await self.chatbot_repository.find_by_id(chatbot_id)
        if not chatbot:
            raise NotFoundError(f"Chatbot with ID {chatbot_id} not found")
        return chatbot

    async def list_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """
        List all chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Chatbot]: List of chatbots
        """
        return await self.chatbot_repository.find_all(skip=skip, limit=limit)

    async def list_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """
        List active chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Chatbot]: List of active chatbots
        """
        return await self.chatbot_repository.find_active_chatbots(skip=skip, limit=limit)

    async def create_chatbot(
        self,
        workspace_id: str,
        name: str,
        model_id: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
    ) -> Chatbot:
        """
        Create new chatbot.

        Args:
            name: Chatbot name
            model_id: Model identifier
            description: Chatbot description
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            system_prompt: System instructions

        Returns:
            Chatbot: Created chatbot

        """
        chatbot = Chatbot(
            id=UUID.generate(),
            workspace_id=workspace_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            is_active=True,
        )

        return await self.chatbot_repository.create(chatbot)

    async def update_chatbot(
        self,
        chatbot_id: str,
        workspace_id: str,
        name: str,
        model_id: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        tools: List[str] = [],
        is_active: Optional[bool] = None
    ) -> Chatbot:
        """
        Update chatbot configuration.

        Args:
            chatbot_id: Chatbot ID
            name: New name (optional)
            description: New description (optional)
            temperature: New temperature (optional)
            max_tokens: New max tokens (optional)
            system_prompt: New system prompt (optional)
            is_active: Active status (optional)

        Returns:
            Chatbot: Updated chatbot domain entity

        Raises:
            NotFoundError: If chatbot not found
        """
        chatbot = await self.get_chatbot_by_id(chatbot_id)

        if workspace_id is not None:
            chatbot.workspace_id = workspace_id
        if name is not None:
            chatbot.name = name
        if model_id is not None:
            chatbot.model_id = model_id
        if description is not None:
            chatbot.description = description
        if temperature is not None:
            chatbot.temperature = temperature
        if max_tokens is not None:
            chatbot.max_tokens = max_tokens
        if system_prompt is not None:
            chatbot.system_prompt = system_prompt
        if len(tools) > 0:
            chatbot.tools = tools
        if is_active is not None:
            if is_active:
                chatbot.activate()
            else:
                chatbot.deactivate()

        return await self.chatbot_repository.update(chatbot)

    async def delete_chatbot(self, chatbot_id: str) -> bool:
        """
        Delete chatbot.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If chatbot not found
        """
        if not await self.chatbot_repository.exists(chatbot_id):
            raise NotFoundError(f"Chatbot with ID {chatbot_id} not found")

        return await self.chatbot_repository.delete(chatbot_id)
