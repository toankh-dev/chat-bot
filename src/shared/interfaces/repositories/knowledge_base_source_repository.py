"""
IKBSourceRepository interface - Contract for knowledge base source operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.postgresql.models.knowledge_base_source_model import (
    KnowledgeBaseSourceModel,
)


class IKnowledgeBaseSourceRepository(ABC):
    """Interface for knowledge base source repository operations."""

    @abstractmethod
    def get_by_kb_and_source(
        self, kb_id: int, source_type: str, source_id: str
    ) -> Optional[KnowledgeBaseSourceModel]:
        """
        Get knowledge base source by KB ID, source type, and source ID.

        Args:
            kb_id: Knowledge base ID
            source_type: Source type (e.g., 'repository')
            source_id: Source identifier

        Returns:
            KnowledgeBaseSource model or None
        """
        pass

    @abstractmethod
    def create(self, source_data: dict) -> KnowledgeBaseSourceModel:
        """
        Create a new knowledge base source.

        Args:
            source_data: Dictionary with source fields

        Returns:
            Created KnowledgeBaseSource model
        """
        pass

    @abstractmethod
    def update(self, entity: KnowledgeBaseSourceModel) -> KnowledgeBaseSourceModel:
        """Update existing Knowledge Base Source from domain entity."""
        pass

    @abstractmethod
    def update_source_sync_status(self, source: KnowledgeBaseSourceModel) -> KnowledgeBaseSourceModel:
        """Update existing Knowledge Base Source from domain entity."""
