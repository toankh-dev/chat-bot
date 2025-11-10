"""
Factory for creating embedding service instances.
"""
from typing import Optional, Dict, Type, List
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from .providers.bedrock_embedding import BedrockEmbeddingService
from .providers.gemini_embedding import GeminiEmbeddingService
from ..bedrock_client import BedrockClient
from core.config import settings
from core.logger import logger


class EmbeddingFactory:
    """Factory for creating embedding service instances."""

    _providers: Dict[str, Type[IEmbeddingService]] = {
        'bedrock': BedrockEmbeddingService,
        'gemini': GeminiEmbeddingService,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[IEmbeddingService]):
        """Register a new embedding provider."""
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, config: Optional[dict] = None, **kwargs) -> IEmbeddingService:
        """
        Create embedding service instance based on configured provider.
        
        Args:
            config: Provider-specific configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            IEmbeddingService: Embedding service instance
        """
        provider = settings.EMBEDDING_PROVIDER
        if provider not in cls._providers:
            raise ValueError(f"Unknown embedding provider: {provider}. Available: {list(cls._providers.keys())}")
            
        provider_cls = cls._providers[provider]
        config = config or {}
        config.update(kwargs)
        
        try:
            if provider == 'bedrock':
                # Allow optional bedrock_client in config; provider will lazily create one if not provided
                bedrock_client = config.get('bedrock_client')
                model_id = config.get('model_id', settings.EMBEDDING_MODEL)
                if not model_id:
                    raise ValueError("model_id is required for bedrock provider")
                return provider_cls(bedrock_client=bedrock_client, model_id=model_id)
                
            elif provider == 'gemini':
                api_key = config.get('api_key')
                model_name = config.get('model_name', settings.EMBEDDING_MODEL)
                if not model_name:
                    raise ValueError("model_name is required for gemini provider")
                return provider_cls(api_key=api_key, model_name=model_name)
                
            else:
                return provider_cls(**config)
                
        except Exception as e:
            raise RuntimeError(f"Failed to create {provider} embedding service: {e}")

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available embedding providers."""
        return ["bedrock", "gemini"]

    @staticmethod
    def get_provider_models() -> dict[str, list[str]]:
        """Get available embedding models for each provider."""
        return {
            "bedrock": [
                "amazon.titan-embed-text-v1",
                "amazon.titan-embed-text-v2:0",
                "cohere.embed-english-v3",
                "cohere.embed-multilingual-v3"
            ],
            "gemini": [
                "models/embedding-001",
                "models/text-embedding-004"
            ]
        }

    @staticmethod
    def get_embedding_dimensions() -> dict[str, int]:
        """Get embedding dimensions for each model."""
        return {
            # Bedrock models
            "amazon.titan-embed-text-v1": 1536,
            "amazon.titan-embed-text-v2:0": 1024,
            "cohere.embed-english-v3": 1024,
            "cohere.embed-multilingual-v3": 1024,

            # Gemini models
            "models/embedding-001": 768,
            "models/text-embedding-004": 768
        }
