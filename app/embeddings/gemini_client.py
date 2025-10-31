"""
GeminiAI Embedding Provider
"""

import os
import logging
from typing import List
import httpx

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Gemini embedding provider using their API
    """

    def __init__(
    self,
    api_key: str = None,
    model: str = "gemini-embedding-001"
    ):
        """
        Initialize GeminiAI client

        Args:
            api_key: GeminiAPI API key (defaults to EMBED_API_KEY env var)
            model: Model name for embedding (default gemini-embedding-001)
        """
        self.api_key = api_key or os.getenv("EMBED_API_KEY")
        if not self.api_key:
            raise ValueError("GeminiAI API key is required. Set EMBED_API_KEY environment variable.")

        self.model = model
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent"

        # Model dimensions map (update if needed)
        self.dimensions = {
            "gemini-embedding-001": 3072,
            "text-embedding-005": 768,
            "text-multilingual-embedding-002": 768,
        }

        logger.info(f"Initialized GeminiAI embedding client with model: {self.model}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using Gemini API

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
                    # GeminiAI returns embeddings in 'data' field
                    embeddings = [item["embedding"] for item in result["data"]]
                    logger.info(f"Generated {len(embeddings)} embeddings using GeminiAI")
                    return embeddings
                else:
                    error_msg = f"GeminiAI API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with GeminiAI: {e}")
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
                logger.info(f"Generated {len(embeddings)} embeddings using GeminiAI (sync)")
                return embeddings
            else:
                error_msg = f"GeminiAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Error generating embeddings with GeminiAI (sync): {e}")
            raise

    def get_dimension(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding dimension
        """
        return self.dimensions.get(self.model, 3072)
