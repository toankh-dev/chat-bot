"""
Groq LLM wrapper for LangChain
Fast and FREE inference with Llama models
"""

import logging
import os
from typing import Any, List, Optional, Mapping
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from groq import Groq

logger = logging.getLogger(__name__)


class GroqLLM(LLM):
    """
    LangChain wrapper for Groq API (Fast & Free)
    """

    api_key: str
    model: str = "llama-3.3-70b-versatile"  # Fast and powerful (latest)
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: int = 60

    @property
    def _llm_type(self) -> str:
        """Return type of LLM"""
        return "groq"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call Groq API

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Calling Groq API ({self.model})")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            # Initialize Groq client
            client = Groq(api_key=self.api_key)

            # Call Groq API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stop=stop
            )

            # Extract response text
            generated_text = response.choices[0].message.content

            logger.info(f"Generated {len(generated_text)} chars from Groq")
            logger.debug(f"Response preview: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get identifying parameters"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


class AsyncGroqLLM(GroqLLM):
    """
    Async version of GroqLLM
    """

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async call to Groq API

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Async calling Groq API ({self.model})")

            # Initialize async Groq client
            from groq import AsyncGroq
            client = AsyncGroq(api_key=self.api_key)

            # Call Groq API asynchronously
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stop=stop
            )

            # Extract response text
            generated_text = response.choices[0].message.content

            logger.info(f"Generated {len(generated_text)} chars from Groq")

            return generated_text

        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            raise
