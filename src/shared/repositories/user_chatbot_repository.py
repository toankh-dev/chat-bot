"""
User-Chatbot repository interface.

Defines the contract for user-chatbot relationship operations.
"""

from abc import ABC, abstractmethod
from typing import List
from src.infrastructure.postgresql.models import User, Chatbot


class UserChatbotRepository(ABC):
    """
    User-Chatbot repository interface.

    Manages the many-to-many relationship between users and chatbots.
    """

    @abstractmethod
    async def assign_chatbot_to_users(
        self, chatbot_id: int, user_ids: List[int], assigned_by: int
    ) -> None:
        """
        Assign chatbot to multiple users.

        Args:
            chatbot_id: Chatbot ID
            user_ids: List of user IDs
            assigned_by: Admin user ID who is making the assignment
        """
        pass

    @abstractmethod
    async def remove_chatbot_from_all_users(self, chatbot_id: int) -> None:
        """
        Remove chatbot from all users.

        Args:
            chatbot_id: Chatbot ID
        """
        pass

    @abstractmethod
    async def get_chatbot_users(self, chatbot_id: int) -> List[int]:
        """
        Get all user IDs a chatbot is assigned to.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            List of user IDs
        """
        pass

    @abstractmethod
    async def get_user_chatbots(self, user_id: int) -> List[int]:
        """
        Get all chatbot IDs assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of chatbot IDs
        """
        pass
