"""
Embedding services for converting text to vector representations.

This module provides embedding implementations for different providers.

Architecture:
    - IEmbeddingService (shared/interfaces) - Domain contract for uniformity
    - utils module - Shared utility functions
    - Provider implementations - Gemini, Bedrock, etc.

Recommended usage:
    # Import implementations
    from infrastructure.ai_services.embeddings import GeminiEmbeddingService

    # Import utilities when needed
    from infrastructure.ai_services.embeddings.utils import (
        validate_text_input,
        numpy_to_list,
        batch_items
    )
"""

from .providers.gemini_embedding import GeminiEmbeddingService
from .providers.bedrock_embedding import BedrockEmbeddingService
from .factory import EmbeddingFactory
from . import utils

__all__ = [
    "BedrockEmbeddingService",
    "GeminiEmbeddingService",
    "EmbeddingFactory",
    "utils"
]
