"""
Bedrock embedding service implementation.
"""
from typing import List, Optional, TYPE_CHECKING
import asyncio

from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from ..utils import validate_text_input, numpy_to_list
if TYPE_CHECKING:
    from ...bedrock_client import BedrockClient
from core.logger import logger


class BedrockEmbeddingService(IEmbeddingService):
    """
    Bedrock implementation of embedding service.

    Implements: IEmbeddingService (domain contract)
    Uses: embedding utilities from utils module (no inheritance needed)
    """

    def __init__(self, bedrock_client: Optional['BedrockClient'], model_id: str):
        """
        Initialize Bedrock embedding service.

        Args:
            bedrock_client: Configured Bedrock client
            model_id: Bedrock model ID for embeddings
        """
        # Lazily instantiate shared BedrockClient if not provided
        if bedrock_client is None:
            from ...bedrock_client import BedrockClient
            bedrock_client = BedrockClient()
        self.client = bedrock_client
        self.model_id = model_id
        self._embedding_dimension = self._get_model_dimension()

    def _get_model_dimension(self) -> int:
        """Get embedding dimension for current model."""
        if "titan" in self.model_id.lower():
            return 1536
        elif "cohere" in self.model_id.lower():
            return 1024
        else:
            return 1024  # Default dimension

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

            # Run sync Bedrock call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    input={"inputText": text}
                )
            )
            embedding = response.get("embedding", [])

            # Convert to list if needed (using utility function)
            if hasattr(embedding, 'tolist'):
                return numpy_to_list(embedding)
            return embedding if isinstance(embedding, list) else list(embedding)
        except Exception as e:
            logger.error(f"Error creating embedding with Bedrock: {e}")
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
