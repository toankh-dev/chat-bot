"""
Gemini LLM service implementation.
"""
from typing import Optional, Dict, Any, List
import asyncio
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from core.config import settings
from core.logger import logger
from shared.interfaces.services.ai_services.llm_service import ILLMService
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

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Initialize Gemini LLM service.

        Args:
            model_name: Name/ID of Gemini model to use
            api_key: Optional API key (can be set via env var)
        """
        if api_key:
            genai.configure(api_key=api_key)
        elif settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        # Set default timeout to 60 seconds
        self.timeout_seconds = 60

    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
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
            validate_generation_parameters(max_tokens, temperature)

            # Build full prompt with context (using utility function)
            full_prompt = build_prompt_with_context(prompt, context)

            # Run sync Gemini call in executor with timeout to avoid blocking
            loop = asyncio.get_event_loop()
            response_text = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.get_completion(
                        prompt=full_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
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
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate streaming response from Gemini LLM.

        Args:
            prompt: User prompt/question
            context: Retrieved context from knowledge base
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Yields:
            Response chunks
        """
        try:
            # Build full prompt with context if provided
            full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}" if context else prompt

            # For now, yield the complete response as single chunk
            # TODO: Implement proper streaming with Gemini streaming API
            response_text = await self.generate_response(
                prompt=prompt,
                context=context,
                max_tokens=max_tokens,
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
        return format_model_info("gemini", self.model_name)

    def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """Get chat completion from Gemini."""
        try:
            chat = self.model.start_chat()
            for message in messages:
                if message["role"] == "user":
                    chat.send_message(message["content"])

            response = chat.last.text
            return response

        except Exception as e:
            logger.error(f"Error getting chat completion from Gemini: {e}")
            raise

    def get_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """Get text completion from Gemini."""
        try:
            generation_config = {}
            if temperature is not None:
                generation_config["temperature"] = temperature
            if max_tokens is not None:
                generation_config["max_output_tokens"] = max_tokens

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None
            )
            return response.text

        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Gemini API request timed out: {e}")
            raise TimeoutError(f"The request timed out. Please try again with a shorter message or try again later.") from e
        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Gemini API service unavailable: {e}")
            raise ConnectionError("The AI service is temporarily unavailable. Please try again in a few moments.") from e
        except Exception as e:
            logger.error(f"Error getting completion from Gemini: {e}")
            raise
