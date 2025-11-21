from abc import  abstractmethod
from typing import List
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService

class BaseEmbeddingService(IEmbeddingService):
    """
    Abstract base class for vector store implementations.
    Provides common interface and shared functionality.
    """

    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Convert texts to vector embeddings."""
        pass
    
    @abstractmethod
    async def create_single_embedding(self, text: str) -> List[float]:
        """Convert single text to vector embedding."""
        pass