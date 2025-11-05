"""
Factory functions for creating LLM and Embedding providers.
"""

import logging
from typing import Optional

from .base import LLMProvider, EmbeddingProvider
from .providers.bedrock_provider import BedrockLLMProvider, BedrockEmbeddingProvider
from .providers.gemini_provider import GeminiLLMProvider, GeminiEmbeddingProvider
from ..config import get_settings

logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_name: Optional[str] = None,
    model_id: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.

    Args:
        provider_name: Provider name ('bedrock', 'gemini'). If None, uses settings.
        model_id: Model ID (optional, uses provider default if not specified)
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMProvider instance
    """
    settings = get_settings()
    provider_name = provider_name or settings.llm_provider

    logger.info(f"Creating LLM provider: {provider_name}")

    if provider_name == 'bedrock':
        return BedrockLLMProvider(model_id=model_id, **kwargs)
    elif provider_name == 'gemini':
        return GeminiLLMProvider(model_id=model_id, **kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: bedrock, gemini"
        )


def get_embedding_provider(
    provider_name: Optional[str] = None,
    model_id: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """
    Factory function to get the appropriate embedding provider.

    Args:
        provider_name: Provider name ('bedrock', 'gemini'). If None, uses settings.
        model_id: Model ID (optional, uses provider default if not specified)
        **kwargs: Additional provider-specific arguments

    Returns:
        EmbeddingProvider instance
    """
    settings = get_settings()
    provider_name = provider_name or settings.llm_provider

    logger.info(f"Creating embedding provider: {provider_name}")

    if provider_name == 'bedrock':
        return BedrockEmbeddingProvider(model_id=model_id, **kwargs)
    elif provider_name == 'gemini':
        return GeminiEmbeddingProvider(model_id=model_id, **kwargs)
    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider_name}. "
            f"Supported providers: bedrock, gemini"
        )


# Convenience functions for backward compatibility
def create_llm_client(**kwargs):
    """
    Legacy function for backward compatibility.
    Use get_llm_provider() instead.
    """
    logger.warning("create_llm_client() is deprecated. Use get_llm_provider() instead.")
    return get_llm_provider(**kwargs)


def create_embedding_client(**kwargs):
    """
    Legacy function for backward compatibility.
    Use get_embedding_provider() instead.
    """
    logger.warning("create_embedding_client() is deprecated. Use get_embedding_provider() instead.")
    return get_embedding_provider(**kwargs)
