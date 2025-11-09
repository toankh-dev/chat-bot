"""
Gemini embedding service implementation.
"""
from typing import List, Optional
import google.generativeai as genai
import asyncio

from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from ..utils import validate_text_input
from core.logger import logger


class GeminiEmbeddingService(IEmbeddingService):
    """
    Gemini implementation of embedding service.

    Implements: IEmbeddingService (domain contract)
    Uses: embedding utilities from utils module (no inheritance needed)
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/embedding-001"):
        """
        Initialize Gemini embedding service.

        Args:
            api_key: Optional API key
            model_name: Embedding model name
        """
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model_name
        self._embedding_dimension = 768  # Fixed for current Gemini models

    async def create_single_embedding(self, text: str) -> List[float]:
        """
        Convert single text to vector embedding.

        Implements IEmbeddingService contract.

        Args:
            text: Text to embed

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
                lambda: genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
            )
            return result['embedding']
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
