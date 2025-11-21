"""
Factory for creating embedding service instances.
"""
from typing import Any, Optional, Dict, Type

from infrastructure.ai_services.gemini_client import GeminiClient
from infrastructure.ai_services.bedrock_client import BedrockClient
from src.infrastructure.ai_services.embeddings.base import BaseEmbeddingService
from .providers.bedrock_embedding import BedrockEmbeddingService
from .providers.gemini_embedding import GeminiEmbeddingService


class EmbeddingFactory:
    """Factory for creating embedding service instances."""

    _providers: Dict[str, Type[BaseEmbeddingService]] = {
        'bedrock': BedrockEmbeddingService,
        'gemini': GeminiEmbeddingService,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseEmbeddingService]):
        """Register a new embedding provider."""
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> BaseEmbeddingService:
        """
        Create embedding service instance based on configured provider.
        
        Args:
            config: Provider-specific configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            IEmbeddingService: Embedding service instance
        """
        if provider not in cls._providers:
            raise ValueError(f"Unknown knowledge base provider: {provider}. Available: {list(cls._providers.keys())}")

        provider_cls = cls._providers[provider]
        cfg = config or {}
        
        if provider == "bedrock":
            client = BedrockClient.create(cfg)
            return provider_cls(bedrock_client=client)

        elif provider == "gemini":
            client = GeminiClient.create(cfg)
            return provider_cls(gemini_client=client)

