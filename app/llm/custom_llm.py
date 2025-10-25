"""
Custom LLM wrapper for LangChain to use our LLM service
"""

import logging
from typing import Any, List, Optional, Mapping
import httpx
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

logger = logging.getLogger(__name__)


class CustomLLM(LLM):
    """
    Custom LLM that calls our LLM service API
    """

    service_url: str
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 120

    @property
    def _llm_type(self) -> str:
        """Return type of LLM"""
        return "custom_llm_service"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the LLM service

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences (not used currently)
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Calling LLM service at {self.service_url}")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            # Prepare request
            request_data = {
                "prompt": prompt,
                "max_new_tokens": kwargs.get("max_new_tokens", self.max_new_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            }

            # Call LLM service
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.service_url}/generate",
                    json=request_data
                )

                if response.status_code != 200:
                    error_msg = f"LLM service returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                result = response.json()
                generated_text = result.get("generated_text", "")

                logger.info(f"Generated {len(generated_text)} chars in {result.get('processing_time', 0):.2f}s")
                logger.debug(f"Response preview: {generated_text[:100]}...")

                return generated_text

        except httpx.TimeoutException:
            logger.error("LLM service request timed out")
            raise Exception("LLM service is taking too long to respond. Please try again.")

        except Exception as e:
            logger.error(f"Error calling LLM service: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get identifying parameters"""
        return {
            "service_url": self.service_url,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }


class AsyncCustomLLM(CustomLLM):
    """
    Async version of CustomLLM
    """

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async call to LLM service

        Args:
            prompt: The prompt to generate from
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Generated text
        """

        try:
            logger.info(f"Async calling LLM service at {self.service_url}")

            # Prepare request
            request_data = {
                "prompt": prompt,
                "max_new_tokens": kwargs.get("max_new_tokens", self.max_new_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
            }

            # Call LLM service asynchronously
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.service_url}/generate",
                    json=request_data
                )

                if response.status_code != 200:
                    error_msg = f"LLM service returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                result = response.json()
                generated_text = result.get("generated_text", "")

                logger.info(f"Generated {len(generated_text)} chars")

                return generated_text

        except httpx.TimeoutException:
            logger.error("LLM service request timed out")
            raise Exception("LLM service timeout")

        except Exception as e:
            logger.error(f"Error calling LLM service: {e}")
            raise
