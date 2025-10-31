"""
Gemini LLM wrapper for LangChain
Free and powerful Google Gemini models
"""

import logging
import os
from typing import Any, List, Optional, Mapping
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiLLM(LLM):
    """
    LangChain wrapper for Google Gemini API
    """

    api_key: str
    model: str = "gemini-2.0-flash-exp"  # Latest Gemini 2.0 model
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60

    @property
    def _llm_type(self) -> str:
        """Return type of LLM"""
        return "gemini"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call Gemini API

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Calling Gemini API ({self.model})")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            # Configure Gemini
            genai.configure(api_key=self.api_key)

            # Initialize model
            model = genai.GenerativeModel(self.model)

            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stop_sequences=stop if stop else None
            )

            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Extract response text
            generated_text = response.text

            logger.info(f"Generated {len(generated_text)} chars from Gemini")
            logger.debug(f"Response preview: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get identifying parameters"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


class AsyncGeminiLLM(GeminiLLM):
    """
    Async version of GeminiLLM
    """

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async call to Gemini API

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Async calling Gemini API ({self.model})")

            # Configure Gemini
            genai.configure(api_key=self.api_key)

            # Initialize model
            model = genai.GenerativeModel(self.model)

            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stop_sequences=stop if stop else None
            )

            # Generate response asynchronously
            response = await model.generate_content_async(
                prompt,
                generation_config=generation_config
            )

            # Extract response text
            generated_text = response.text

            logger.info(f"Generated {len(generated_text)} chars from Gemini")

            return generated_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
