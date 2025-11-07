"""
Group-Chatbot repository interface.

Defines the contract for group-chatbot relationship operations.
"""

from abc import ABC, abstractmethod
from typing import List
from src.infrastructure.postgresql.models import Group, Chatbot


class GroupChatbotRepository(ABC):
    """
    Group-Chatbot repository interface.

    Manages the many-to-many relationship between groups and chatbots.
    """

    @abstractmethod
    async def assign_chatbot_to_groups(
        self, chatbot_id: int, group_ids: List[int], assigned_by: int
    ) -> None:
        """
        Assign chatbot to multiple groups.

        Args:
            chatbot_id: Chatbot ID
            group_ids: List of group IDs
            assigned_by: Admin user ID who is making the assignment
        """
        pass

    @abstractmethod
    async def remove_chatbot_from_all_groups(self, chatbot_id: int) -> None:
        """
        Remove chatbot from all groups.

        Args:
            chatbot_id: Chatbot ID
        """
        pass

    @abstractmethod
    async def get_chatbot_groups(self, chatbot_id: int) -> List[Group]:
        """
        Get all groups a chatbot is assigned to.

        Args:
            chatbot_id: Chatbot ID

        Returns:
            List of Group objects
        """
        pass

    @abstractmethod
    async def get_group_chatbots(self, group_id: int) -> List[int]:
        """
        Get all chatbot IDs assigned to a group.

        Args:
            group_id: Group ID

        Returns:
            List of chatbot IDs
        """
        pass
