"""
Embedding providers
"""

from .base import EmbeddingProvider
from .voyage_client import VoyageEmbeddingProvider
from .local_client import LocalEmbeddingProvider

__all__ = ['EmbeddingProvider', 'VoyageEmbeddingProvider', 'LocalEmbeddingProvider']
