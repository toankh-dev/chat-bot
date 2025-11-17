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

    @abstractmethod
    def create_domain_specific(self, domain: str, **config) -> IVectorStore:
        """
        Create domain-specific vector store instance.

        Args:
            domain: Domain name (healthcare, education, gitlab, etc.)
            **config: Additional configuration

        Returns:
            IVectorStore: Domain-specific vector store instance
        """
        pass

    @abstractmethod
    def get_available_providers(self) -> List[str]:
        """
        Get list of available vector store providers.

        Returns:
            List[str]: Available provider names
        """
        pass
