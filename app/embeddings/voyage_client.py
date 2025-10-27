"""
VoyageAI Embedding Provider
"""

import os
import logging
from typing import List
import httpx

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class VoyageEmbeddingProvider(EmbeddingProvider):
    """
    VoyageAI embedding provider using their API
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "voyage-2"
    ):
        """
        Initialize VoyageAI client

        Args:
            api_key: VoyageAI API key (defaults to VOYAGE_API_KEY env var)
            model: Model name (voyage-2, voyage-code-2, voyage-large-2)
        """
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("VoyageAI API key is required. Set VOYAGE_API_KEY environment variable.")

        self.model = model
        self.api_url = "https://api.voyageai.com/v1/embeddings"

        # Model dimensions
        self.dimensions = {
            "voyage-2": 1024,
            "voyage-code-2": 1536,
            "voyage-large-2": 1536,
            "voyage-lite-02-instruct": 1024
        }

        logger.info(f"Initialized VoyageAI embedding provider with model: {self.model}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using VoyageAI API

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": texts,
                        "model": self.model
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    # VoyageAI returns embeddings in 'data' field
                    embeddings = [item["embedding"] for item in result["data"]]
                    logger.info(f"Generated {len(embeddings)} embeddings using VoyageAI")
                    return embeddings
                else:
                    error_msg = f"VoyageAI API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with VoyageAI: {e}")
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
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": texts,
                    "model": self.model
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                logger.info(f"Generated {len(embeddings)} embeddings using VoyageAI (sync)")
                return embeddings
            else:
                error_msg = f"VoyageAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with VoyageAI (sync): {e}")
            raise

    def get_dimension(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding dimension
        """
        return self.dimensions.get(self.model, 1024)
