"""
Chatbot repository interface.

Defines the contract for chatbot data access operations.
"""

from abc import abstractmethod
from typing import List, Optional
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.chatbot import ChatbotEntity


class ChatbotRepository(BaseRepository[ChatbotEntity, str]):
    """
    Chatbot repository interface.
    """

    @abstractmethod
    async def find_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """
        Find all active chatbots with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active chatbot entities
        """
        pass

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: str, skip: int = 0, limit: int = 100
    ) -> List[ChatbotEntity]:
        """
        Find chatbots in a specific workspace.

        Args:
            workspace_id: Workspace identifier
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of chatbot entities in the workspace
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[ChatbotEntity]:
        """Find chatbot by ID."""
        # Ensure ID is an integer
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[ChatbotEntity]:
        """Find all chatbots with pagination."""
        pass

    @abstractmethod
    async def create(
        self,
        entity: ChatbotEntity,
        created_by: int,
        model_id: int,
        top_p=None,
        welcome_message: str = None,
        fallback_message: str = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
    ) -> ChatbotEntity:
        """
        Create new chatbot.

        Args:
            entity: Chatbot domain entity
            created_by: User ID who created the chatbot
            model_id: AI model ID
            top_p: Top-p sampling parameter
            welcome_message: Welcome message
            fallback_message: Fallback message
            max_conversation_length: Max conversation length
            enable_function_calling: Enable function calling
        """
        pass

    @abstractmethod
    async def update(
        self,
        entity: ChatbotEntity,
        created_by: int,
        model_id: Optional[int] = None,
        top_p=None,
        welcome_message: str = None,
        fallback_message: str = None,
        max_conversation_length: int = 50,
        enable_function_calling: bool = True,
    ) -> ChatbotEntity:
        """Update existing chatbot."""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete chatbot by ID."""
        pass

    @abstractmethod
    async def exists(self, id: int) -> bool:
        """Check if chatbot exists."""
        pass
