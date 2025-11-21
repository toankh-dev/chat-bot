"""
IVectorStoreFactory interface - Contract for vector store factory operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore


class IVectorStoreFactory(ABC):
    """Interface for vector store factory."""

    @abstractmethod
    def create(self, config: Optional[dict] = None, **kwargs) -> IVectorStore:
        """
        Create a vector store instance with given configuration.

        Args:
            config: Configuration dictionary for the vector store
            **kwargs: Additional keyword arguments

        Returns:
            IVectorStore: Vector store instance

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If vector store creation fails
        """
        pass
