from abc import ABC, abstractmethod
from typing import List

class IEmbeddingService(ABC):
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Convert texts to vector embeddings."""
        pass
    
    @abstractmethod
    async def create_single_embedding(self, text: str) -> List[float]:
        """Convert single text to vector embedding."""
        pass