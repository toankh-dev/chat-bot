"""
EmbeddingIndex repository interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.embedding_index import EmbeddingIndexEntity

class EmbeddingIndexRepository(ABC):
    @abstractmethod
    async def create(self, embedding: EmbeddingIndexEntity) -> EmbeddingIndexEntity:
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[EmbeddingIndexEntity]:
        pass

    @abstractmethod
    async def find_by_user(self, user_id: int) -> List[EmbeddingIndexEntity]:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
