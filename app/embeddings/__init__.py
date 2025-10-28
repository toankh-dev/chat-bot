"""
Embedding providers
"""

from .base import EmbeddingProvider
from .voyage_client import VoyageEmbeddingProvider

__all__ = ['EmbeddingProvider', 'VoyageEmbeddingProvider']
