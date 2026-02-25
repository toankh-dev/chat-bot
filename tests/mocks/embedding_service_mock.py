"""
Mock implementation of EmbeddingService for testing.
"""
from typing import List
import hashlib


class EmbeddingServiceMock:
    """Mock embedding service that generates deterministic fake embeddings."""

    def __init__(self, embedding_dimension: int = 768):
        """
        Initialize mock embedding service.

        Args:
            embedding_dimension: Dimension of embedding vectors
        """
        self.embedding_dimension = embedding_dimension

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create mock embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of mock embedding vectors
        """
        return [await self.create_single_embedding(text) for text in texts]

    async def create_single_embedding(self, text: str) -> List[float]:
        """
        Create mock embedding for a single text.
        Uses hash of text to generate deterministic but unique embeddings.

        Args:
            text: Text to embed

        Returns:
            Mock embedding vector
        """
        # Use hash of text to generate deterministic embedding
        text_hash = hashlib.md5(text.encode()).digest()

        # Generate embedding vector from hash
        embedding = []
        for i in range(self.embedding_dimension):
            # Use hash bytes cyclically to generate values between -1 and 1
            byte_value = text_hash[i % len(text_hash)]
            normalized_value = (byte_value / 255.0) * 2 - 1  # Scale to [-1, 1]
            embedding.append(normalized_value)

        return embedding
