from abc import ABC, abstractmethod
from typing import List, Any

class IVectorStore(ABC):
    @abstractmethod
    def add_vector(self, vector: List[float], metadata: dict) -> str:
        """Add a vector to the store and return its ID."""
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int = 5) -> List[Any]:
        """Query the store for similar vectors."""
        pass
