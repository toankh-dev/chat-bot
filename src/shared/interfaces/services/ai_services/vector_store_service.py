from abc import ABC, abstractmethod
from typing import List, Any, Dict

class IVectorStore(ABC):
    @abstractmethod
    def add_vector(self, vector: List[float], metadata: dict, document: str) -> str:
        """Add a vector with metadata and return its ID."""
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Query vectors and return structured results."""
        pass
