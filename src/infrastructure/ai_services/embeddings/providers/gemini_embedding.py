"""
Gemini embedding service implementation.
"""
from typing import List
import asyncio

from infrastructure.ai_services.gemini_client import GeminiClient
from infrastructure.ai_services.embeddings.base import BaseEmbeddingService
from ..utils import validate_text_input
from core.logger import logger


class GeminiEmbeddingService(BaseEmbeddingService):
    """
    Gemini implementation of embedding service.

    Implements: IEmbeddingService (domain contract)
    Uses: embedding utilities from utils module (no inheritance needed)
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Gemini embedding service.

        Args:
            api_key: Optional API key
            model_name: Embedding model name
        """
        self.client = gemini_client
        self._embedding_dimension = 768

    async def create_single_embedding(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Convert single text to vector embedding.

        Implements IEmbeddingService contract.

        Args:
            text: Text to embed
            task_type: Gemini task type for optimization
                - "retrieval_document": Optimize for storing documents (default)
                - "retrieval_query": Optimize for search queries
                - "semantic_similarity": Optimize for similarity comparison

        Returns:
            List[float]: Vector embedding
        """
        try:
            # Validate input (using utility function - no inheritance needed)
            validate_text_input(text)

            # Run sync API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.embed(
                    text=text,
                    task_type=task_type
                )
            )
            return result
        except Exception as e:
            logger.error(f"Error creating embedding with Gemini: {e}")
            raise

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Convert texts to vector embeddings.

        Implements IEmbeddingService contract.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of vector embeddings
        """
        tasks = [self.create_single_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self._embedding_dimension
