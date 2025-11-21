from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IRAGService(ABC):
    """Interface for RAG (Retrieval-Augmented Generation) services."""
    
    @abstractmethod
    async def retrieve_contexts(self, query: str, domain: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant contexts for query."""
        pass
