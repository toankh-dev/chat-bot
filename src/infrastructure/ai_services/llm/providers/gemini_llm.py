"""
Gemini LLM service implementation.
"""
from typing import Optional, Dict, Any, List
import asyncio
from google.api_core import exceptions as google_exceptions
from core.logger import logger
from shared.interfaces.services.ai_services.llm_service import ILLMService
from infrastructure.ai_services.gemini_client import GeminiClient
from ..utils import (
    build_prompt_with_context,
    validate_generation_parameters,
    validate_prompt_input,
    format_model_info
)


class GeminiLLMService(ILLMService):
    """
    Gemini implementation of LLM service.

    Implements: ILLMService (domain contract)
    Uses: LLM utilities from utils module (no inheritance needed)
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Gemini LLM service.

        Args:
            model_name: Name/ID of Gemini model to use
            api_key: Optional API key (can be set via env var)
        """
        self.timeout_seconds = 60
        self.gemini_client = gemini_client

    async def generate_response(
        self,
        prompt: str,
        max_output_tokens,
        temperature,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate response from Gemini LLM.

        Args:
            prompt: User prompt/question
            context: Retrieved context from knowledge base
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response string
        """
        try:
            # Validate inputs (using utility functions)
            validate_prompt_input(prompt)
            validate_generation_parameters(max_output_tokens, temperature)


            # Run sync Gemini call in executor with timeout to avoid blocking
            loop = asyncio.get_event_loop()
            response_text = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.get_completion(
                        prompt=prompt,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        **kwargs
                    )
                ),
                timeout=self.timeout_seconds
            )
            return response_text

        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error in Gemini response generation after {self.timeout_seconds} seconds: {e}")
            raise TimeoutError(f"The request timed out after {self.timeout_seconds} seconds. Please try again with a shorter message or try again later.") from e
        except TimeoutError as e:
            logger.error(f"Timeout error in Gemini response generation: {e}")
            raise
        except ConnectionError as e:
            logger.error(f"Connection error in Gemini response generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise

    async def generate_streaming_response(
        self,
        prompt: str,
        max_output_tokens: int,
        temperature: float,
        context: Optional[str] = None,
        **kwargs
    ):
        """
        Generate streaming response from Gemini LLM.

        Args:
            prompt: User prompt/question
            context: Retrieved context from knowledge base
            max_output_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Yields:
            Response chunks
        """
        try:
            response_text = await self.generate_response(
                prompt=prompt,
                context=context,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                **kwargs
            )
            yield response_text

        except Exception as e:
            logger.error(f"Error generating streaming response from Gemini: {e}")
            raise

    def get_provider_name(self) -> str:
        """Get the name of the LLM provider."""
        return "gemini"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return format_model_info("gemini", self.gemini_client.model_name)

    def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Any:
        """Get chat completion from Gemini."""
        try:
            # Convert messages to google-genai format
            contents = []
            for message in messages:
                role = "user" if message["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": message["content"]}]})

            config = {}
            if temperature is not None:
                config["temperature"] = temperature
            if max_output_tokens is not None:
                config["max_output_tokens"] = max_output_tokens

            response_text = self.gemini_client.generate(
                prompt=contents,
                config=config if config else None
            )
            return response_text

        except Exception as e:
            logger.error(f"Error getting chat completion from Gemini: {e}")
            raise

    def get_completion(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Get text completion from Gemini."""
        try:
            response_text = self.gemini_client.generate(
                prompt=prompt,
                config=kwargs if kwargs else None
            )
            return response_text

        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Gemini API request timed out: {e}")
            raise TimeoutError(f"The request timed out. Please try again with a shorter message or try again later.") from e
        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Gemini API service unavailable: {e}")
            raise ConnectionError("The AI service is temporarily unavailable. Please try again in a few moments.") from e
        except Exception as e:
            logger.error(f"Error getting completion from Gemini: {e}")
            raise
