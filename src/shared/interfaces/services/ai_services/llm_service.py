"""
LLM (Large Language Model) service interface.

This interface defines the contract that all LLM implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ILLMService(ABC):
    """
    Interface for LLM service implementations.

    All LLM providers (Bedrock, Gemini, OpenAI, etc.) must implement this interface
    to ensure consistency and interchangeability.
    """

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
            context: Retrieved context from knowledge base (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            str: Generated response text

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If LLM call fails
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
            context: Retrieved context from knowledge base (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            **kwargs: Additional provider-specific parameters

        Yields:
            str: Response chunks

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If LLM call fails
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the LLM provider.

        Returns:
            str: Provider name (e.g., 'bedrock', 'gemini', 'openai')
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict containing model metadata:
                - provider: Provider name
                - model_id/model_name: Model identifier
                - Additional provider-specific metadata
        """
        pass
