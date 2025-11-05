"""
Google Gemini LLM and Embedding Provider implementation.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")

from ..base import LLMProvider, EmbeddingProvider, LLMResponse, EmbeddingResponse
from ...config import get_settings

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    """Google Gemini LLM provider implementation."""

    def __init__(self, model_id: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Gemini LLM provider.

        Args:
            model_id: Gemini model ID (defaults to settings)
            api_key: Google API key (defaults to settings)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai is required for Gemini provider. "
                "Install with: pip install google-generativeai"
            )

        self.settings = get_settings()
        self._model_id = model_id or self.settings.gemini_model
        self._api_key = api_key or self.settings.gemini_api_key

        if not self._api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Configure Gemini
        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel(self._model_id)

        logger.info(f"Initialized Gemini client for model {self._model_id}")

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion using Gemini."""
        try:
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.95),
                top_k=kwargs.get('top_k', 40),
            )

            # Build prompt with system prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate response
            response = self._model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )

            # Extract content
            content = response.text if hasattr(response, 'text') else ""

            # Extract usage metadata
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    'input_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'output_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                }

            # Extract finish reason
            finish_reason = None
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)

            return LLMResponse(
                content=content,
                model=self._model_id,
                usage=usage,
                finish_reason=finish_reason,
                metadata={'response': response}
            )

        except Exception as e:
            logger.error(f"Gemini LLM error: {e}")
            raise

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Multi-turn chat completion using Gemini."""
        try:
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.95),
                top_k=kwargs.get('top_k', 40),
            )

            # Convert messages to Gemini format
            chat_history = []
            for msg in messages[:-1]:  # All except last message
                role = "user" if msg['role'] == 'user' else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg['content']]
                })

            # Start chat with history
            chat = self._model.start_chat(history=chat_history)

            # Send last message
            last_message = messages[-1]['content']
            response = chat.send_message(
                last_message,
                generation_config=generation_config
            )

            # Extract content
            content = response.text if hasattr(response, 'text') else ""

            # Extract usage metadata
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    'input_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'output_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                }

            # Extract finish reason
            finish_reason = None
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)

            return LLMResponse(
                content=content,
                model=self._model_id,
                usage=usage,
                finish_reason=finish_reason,
                metadata={'response': response}
            )

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """Stream text completion using Gemini."""
        try:
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.95),
                top_k=kwargs.get('top_k', 40),
            )

            # Build prompt with system prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate response with streaming
            response = self._model.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )

            # Stream chunks
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini Embedding provider implementation."""

    def __init__(self, model_id: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Gemini Embedding provider.

        Args:
            model_id: Gemini embedding model ID (defaults to settings)
            api_key: Google API key (defaults to settings)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai is required for Gemini provider. "
                "Install with: pip install google-generativeai"
            )

        self.settings = get_settings()
        self._model_id = model_id or self.settings.gemini_embed_model
        self._api_key = api_key or self.settings.gemini_api_key

        if not self._api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Configure Gemini
        genai.configure(api_key=self._api_key)

        logger.info(f"Initialized Gemini embedding client for model {self._model_id}")

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def dimension(self) -> int:
        """Gemini text-embedding-004 has 768 dimensions."""
        if "text-embedding-004" in self._model_id:
            return 768
        return 768  # Default

    def embed_text(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embedding for a single text."""
        try:
            # Generate embedding
            result = genai.embed_content(
                model=self._model_id,
                content=text,
                task_type=kwargs.get('task_type', 'retrieval_document')
            )

            # Extract embedding
            embedding = result['embedding']

            return EmbeddingResponse(
                embedding=embedding,
                model=self._model_id,
                usage=None,  # Gemini doesn't provide token usage for embeddings
                metadata={'result': result}
            )

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    def embed_batch(self, texts: List[str], **kwargs) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts."""
        try:
            # Gemini supports batch embeddings
            result = genai.embed_content(
                model=self._model_id,
                content=texts,
                task_type=kwargs.get('task_type', 'retrieval_document')
            )

            # Extract embeddings
            embeddings = result['embedding']

            # Return list of responses
            return [
                EmbeddingResponse(
                    embedding=emb,
                    model=self._model_id,
                    usage=None,
                    metadata={'result': result}
                )
                for emb in embeddings
            ]

        except Exception as e:
            logger.error(f"Gemini batch embedding error: {e}")
            # Fallback to sequential processing
            logger.info("Falling back to sequential embedding processing")
            return [self.embed_text(text, **kwargs) for text in texts]
