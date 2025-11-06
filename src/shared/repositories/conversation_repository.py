"""
Conversation repository interface.

Defines the contract for conversation data access operations.
"""

from abc import abstractmethod
from typing import Optional, List
from src.shared.repositories.base_repository import BaseRepository


# Import the Conversation domain entity
from src.domain.entities.conversation import Conversation


class ConversationRepository(BaseRepository[Conversation, str]):
    """
    Conversation repository interface.

    Defines operations specific to conversation entities beyond the base CRUD operations.
    Note: This interface uses the Conversation domain entity, decoupled from any ORM/DB model.
    """

    @abstractmethod
    async def find_by_id_with_messages(self, id: str) -> Optional[Conversation]:
        """
        Find conversation by ID with all messages eagerly loaded.

        Args:
            id: Conversation identifier

        Returns:
            Conversation entity with messages if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """
        Find conversations by user ID with pagination.

        Args:
            user_id: User identifier
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of conversation entities for the user
        """
        pass

    @abstractmethod
    async def find_by_user_and_chatbot(self, user_id: str, chatbot_id: str) -> List[Conversation]:
        """
        Find conversations between a specific user and chatbot.

        Args:
            user_id: User identifier
            chatbot_id: Chatbot identifier

        Returns:
            List of conversation entities between the user and chatbot
        """
        pass
