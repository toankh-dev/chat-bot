"""
Message repository interface.

Defines the contract for message data access operations.
"""

from abc import abstractmethod
from typing import List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.message import Message


class MessageRepository(BaseRepository[Message, str]):
    """
    Message repository interface.

    Defines operations specific to message entities beyond the base CRUD operations.
    """

    @abstractmethod
    async def find_by_conversation(self, conversation_id: str) -> List[Message]:
        """
        Find all messages in a conversation ordered by creation time.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of message entities in chronological order
        """
        pass
