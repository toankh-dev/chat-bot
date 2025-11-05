"""
Base abstract classes for LLM and Embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None  # e.g., {'input_tokens': 100, 'output_tokens': 50}
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """Standardized response from embedding providers."""
    embedding: List[float]
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All LLM providers must implement these methods.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated text and metadata
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Multi-turn chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{'role': 'user', 'content': 'Hello'}]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated text and metadata
        """
        pass

    @abstractmethod
    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Stream text completion from prompt.

        Args:
            prompt: User prompt/message
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 1.0)
            **kwargs: Provider-specific parameters

        Yields:
            Text chunks as they are generated
        """
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'bedrock', 'gemini')."""
        pass


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    All embedding providers must implement these methods.
    """

    @abstractmethod
    def embed_text(self, text: str, **kwargs) -> EmbeddingResponse:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed
            **kwargs: Provider-specific parameters

        Returns:
            EmbeddingResponse with vector and metadata
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str], **kwargs) -> List[EmbeddingResponse]:
        """
        Generate embedding vectors for multiple texts (batch processing).

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of EmbeddingResponse objects
        """
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the embedding model identifier."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'bedrock', 'gemini')."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        pass
