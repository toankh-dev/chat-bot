from typing import Optional, Dict, Any, List, AsyncGenerator
from google import genai
from core.config import settings
from core.logger import logger

class GeminiClient:
    """
    Wrapper for Google Gemini (text + embedding) similar to BedrockClient.

    Services (LLM, Embedding) just receive this instance and use it.
    Model and embedding model are configured inside the client.
    """

    def __init__(
        self,
        **kwargs
    ):  
        
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = kwargs.get("model_name", settings.GEMINI_MODEL)
        self.embedding_model = settings.EMBEDDING_MODEL
        self.timeout_seconds = 60

        # Initialize Google Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self._embedding_dimension = 768

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None, **kwargs) -> "GeminiClient":
        """
        Factory method to create a GeminiClient with dynamic configuration.

        Args:
            config: Dict containing optional keys: api_key, model_name, embedding_model
            **kwargs: Additional options for genai.Client

        Returns:
            GeminiClient instance
        """
        cfg = config or {}
        return cls(
            **{**cfg, **kwargs}
        )

    # ------------------------------
    # Text generation (synchronous)
    # ------------------------------
    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            # config= kwargs if kwargs else None
        )
        try:
            if hasattr(response, "text") and response.text:
                return response.text

            if hasattr(response, "candidates"):
                parts = response.candidates[0].content.parts
                text_chunks = []

                for p in parts:
                    if hasattr(p, "text") and p.text:
                        text_chunks.append(p.text)

                return "".join(text_chunks)

        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")

        return ""

    # ------------------------------
    # Text generation (async streaming)
    # ------------------------------
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        stream = self.client.models.generate_content(
            stream=True,
            model=self.model_name,
            contents=prompt,
            config=kwargs if kwargs else None
        )

        async for chunk in stream:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text

    # ------------------------------
    # Embeddings
    # ------------------------------
    def embed(self, text: str, **kwargs) -> List[float]:
        emb = self.client.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=kwargs if kwargs else None
        )
        return emb.embeddings[0].values if hasattr(emb, "embeddings") else emb["embedding"]

    def get_embedding_dimension(self) -> int:
        """Return embedding dimension (fixed 768 for Gemini)."""
        return self._embedding_dimension


# ------------------------------
# Factory function
# ------------------------------
def get_gemini_client(config: Optional[Dict[str, Any]] = None, **kwargs) -> GeminiClient:
    """
    Factory helper to create a GeminiClient from dynamic config.
    """
    cfg = config or {}
    return GeminiClient.create(cfg, **kwargs)
