from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IRAGService(ABC):
    """Interface for RAG (Retrieval-Augmented Generation) services."""
    
    @abstractmethod
    async def retrieve_and_generate(self, query: str, domain: str = "general", top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant contexts and generate response."""
        pass
    
    @abstractmethod
    async def retrieve_contexts(self, query: str, domain: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant contexts for query."""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: str = None, 
        max_tokens: int = 1000, 
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using LLM (with optional context)."""
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self, 
        prompt: str, 
        context: str = None, 
        max_tokens: int = 1000, 
        temperature: float = 0.7,
        **kwargs
    ):
        """Generate streaming response using LLM."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get current LLM provider name."""
        pass