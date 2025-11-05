"""
Chatbot service.

Handles chatbot management business logic.
"""

from typing import List, Optional
from decimal import Decimal
from src.infrastructure.postgresql.chatbot_repository_impl import ChatbotRepositoryImpl
from src.infrastructure.postgresql.models import Chatbot
from src.core.errors import NotFoundError, ValidationError


class ChatbotService:
    """
    Service for chatbot management operations.
    """

    def __init__(self, chatbot_repository: ChatbotRepositoryImpl):
        self.chatbot_repository = chatbot_repository

    async def get_chatbot_by_id(self, chatbot_id: int) -> Chatbot:
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
        name: str,
        provider: str,
        model: str,
        api_key_encrypted: str,
        created_by: int,
        description: Optional[str] = None,
        temperature: Decimal = Decimal("0.7"),
        max_tokens: int = 2048,
        top_p: Decimal = Decimal("1.0"),
        system_prompt: Optional[str] = None,
        welcome_message: Optional[str] = None,
        fallback_message: Optional[str] = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
        api_base_url: Optional[str] = None
    ) -> Chatbot:
        """
        Create new chatbot.

        Args:
            name: Chatbot name
            provider: LLM provider (openai, anthropic, google)
            model: Model identifier
            api_key_encrypted: Encrypted API key
            created_by: User ID who creates the chatbot
            description: Chatbot description
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            top_p: Nucleus sampling parameter
            system_prompt: System instructions
            welcome_message: Initial message
            fallback_message: Error fallback message
            max_conversation_length: Context window size
            enable_function_calling: Enable tool use
            api_base_url: Custom API endpoint

        Returns:
            Chatbot: Created chatbot

        Raises:
            ValidationError: If validation fails
        """
        if provider not in ["openai", "anthropic", "google"]:
            raise ValidationError(f"Invalid provider: {provider}")

        chatbot = Chatbot(
            name=name,
            description=description,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            system_prompt=system_prompt,
            welcome_message=welcome_message,
            fallback_message=fallback_message,
            max_conversation_length=max_conversation_length,
            enable_function_calling=enable_function_calling,
            api_key_encrypted=api_key_encrypted,
            api_base_url=api_base_url,
            created_by=created_by,
            status="active"
        )

        return await self.chatbot_repository.create(chatbot)

    async def update_chatbot(
        self,
        chatbot_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        temperature: Optional[Decimal] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[Decimal] = None,
        system_prompt: Optional[str] = None,
        welcome_message: Optional[str] = None,
        fallback_message: Optional[str] = None,
        max_conversation_length: Optional[int] = None,
        enable_function_calling: Optional[bool] = None,
        status: Optional[str] = None
    ) -> Chatbot:
        """
        Update chatbot configuration.

        Args:
            chatbot_id: Chatbot ID
            name: New name (optional)
            description: New description (optional)
            temperature: New temperature (optional)
            max_tokens: New max tokens (optional)
            top_p: New top_p (optional)
            system_prompt: New system prompt (optional)
            welcome_message: New welcome message (optional)
            fallback_message: New fallback message (optional)
            max_conversation_length: New context window (optional)
            enable_function_calling: Enable/disable tools (optional)
            status: New status (optional)

        Returns:
            Chatbot: Updated chatbot

        Raises:
            NotFoundError: If chatbot not found
        """
        chatbot = await self.get_chatbot_by_id(chatbot_id)

        if name is not None:
            chatbot.name = name
        if description is not None:
            chatbot.description = description
        if temperature is not None:
            chatbot.temperature = temperature
        if max_tokens is not None:
            chatbot.max_tokens = max_tokens
        if top_p is not None:
            chatbot.top_p = top_p
        if system_prompt is not None:
            chatbot.system_prompt = system_prompt
        if welcome_message is not None:
            chatbot.welcome_message = welcome_message
        if fallback_message is not None:
            chatbot.fallback_message = fallback_message
        if max_conversation_length is not None:
            chatbot.max_conversation_length = max_conversation_length
        if enable_function_calling is not None:
            chatbot.enable_function_calling = enable_function_calling
        if status is not None:
            if status not in ["active", "disabled", "archived"]:
                raise ValidationError(f"Invalid status: {status}")
            chatbot.status = status

        return await self.chatbot_repository.update(chatbot)

    async def delete_chatbot(self, chatbot_id: int) -> bool:
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
