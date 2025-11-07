from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseLLMService(ABC):
    """Base abstract class for LLM services."""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: User prompt/question
            context: Retrieved context from knowledge base
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response string
        """
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate streaming response from LLM.
        
        Args:
            prompt: User prompt/question
            context: Retrieved context from knowledge base
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Response chunks
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the LLM provider."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass