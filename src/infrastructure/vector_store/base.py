from abc import ABC, abstractmethod
from typing import List, Any, Dict
from shared.interfaces.services.ai_services.vector_store_service import IVectorStore

class BaseVectorStore(IVectorStore):
    """
    Abstract base class for vector store implementations.
    Provides common interface and shared functionality.
    """
    
    @abstractmethod
    def add_vector(self, vector: List[float], metadata: dict) -> str:
        """Add a vector with metadata and return its ID."""
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query vectors and return structured results."""
        pass
    
    @abstractmethod
    def get_context_by_id(self, context_id: str) -> Dict[str, Any]:
        """Retrieve specific context by ID."""
        pass
    
    @abstractmethod
    def store_contexts(self, contexts: List[Dict[str, Any]], source_id: str = "") -> List[str]:
        """Store multiple contexts from knowledge base or other sources."""
        pass
    
    # Common utility methods that can be overridden
    def validate_metadata(self, metadata: dict) -> bool:
        """Validate metadata structure."""
        required_fields = ["text"]
        return all(field in metadata for field in required_fields)
    
    def format_context_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format context for consistent response structure."""
        return {
            "id": context.get("context_id", context.get("id", "")),
            "text": context.get("text", ""),
            "source": context.get("source", context.get("source_location", "")),
            "score": context.get("retrieval_score", context.get("score", 0.0)),
            "metadata": context.get("metadata", {})
        }
    
    def get_storage_type(self) -> str:
        """Return the storage type identifier."""
        return self.__class__.__name__.lower().replace("vectorstore", "")
