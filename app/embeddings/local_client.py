"""
Local Embedding Provider (using embedding-service)
"""

import logging
from typing import List
import httpx

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using the embedding service
    """

    def __init__(
        self,
        service_url: str = "http://embedding-service:8000"
    ):
        """
        Initialize local embedding client

        Args:
            service_url: URL of the local embedding service
        """
        self.service_url = service_url
        self._dimension = None

        logger.info(f"Initialized local embedding provider at: {self.service_url}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using local service

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.service_url}/embed",
                    json={"texts": texts, "normalize": True}
                )

                if response.status_code == 200:
                    result = response.json()
                    if self._dimension is None:
                        self._dimension = result.get("dimension", 384)
                    return result["embeddings"]
                else:
                    error_msg = f"Embedding service error: {response.status_code}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with local service: {e}")
            raise

    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous version of embed_texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        import requests

        try:
            response = requests.post(
                f"{self.service_url}/embed",
                json={"texts": texts, "normalize": True},
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if self._dimension is None:
                    self._dimension = result.get("dimension", 384)
                return result["embeddings"]
            else:
                error_msg = f"Embedding service error: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with local service (sync): {e}")
            raise

    def get_dimension(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding dimension
        """
        return self._dimension or 384
