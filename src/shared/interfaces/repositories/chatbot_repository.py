"""
Chatbot repository interface.

Defines the contract for chatbot data access operations.
"""

from abc import abstractmethod
from typing import Optional, List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.chatbot import Chatbot


class ChatbotRepository(BaseRepository[Chatbot, str]):
    """
    Chatbot repository interface.

    Defines operations specific to chatbot entities beyond the base CRUD operations.
    """

    @abstractmethod
    async def find_active_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
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
    async def find_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Chatbot]:
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
