"""
IKnowledgeBaseRepository interface - Contract for knowledge base operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.postgresql.models.knowledge_base_model import KnowledgeBaseModel


class IKnowledgeBaseRepository(ABC):
    """Interface for knowledge base repository operations."""

    @abstractmethod
    def get_by_name_and_chatbot(
        self, kb_name: str, chatbot_id: int
    ) -> Optional[KnowledgeBaseModel]:
        """
        Get knowledge base by name and chatbot ID.

        Args:
            kb_name: Knowledge base name
            chatbot_id: Chatbot ID

        Returns:
            KnowledgeBase model or None
        """
        pass

    @abstractmethod
    def create(self, kb_data: dict) -> KnowledgeBaseModel:
        """
        Create a new knowledge base.

        Args:
            kb_data: Dictionary with KB fields (chatbot_id, name, description, etc.)

        Returns:
            Created KnowledgeBase model
        """
        pass

    @abstractmethod
    def get_by_id(self, kb_id: int) -> Optional[KnowledgeBaseModel]:
        """
        Get knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            KnowledgeBase model or None
        """
        pass

    @abstractmethod
    def get_or_create(
        self,
        knowledge_base_id: int,
        defaults: dict = None
    ) -> tuple[KnowledgeBaseModel, bool]:
        """
        Get existing knowledge base or create new one.

        Args:
            knowledge_base_id: knowledge base ID
            defaults: Default values if creating new knowledge base

        Returns:
            Tuple of (knowledge base, created) where created is True if new
        """
        pass