"""
Bedrock LLM service implementation.
"""
from typing import Optional, Dict, Any, List
import asyncio
from botocore.config import Config
from core.config import settings
from core.logger import logger
from shared.interfaces.services.ai_services.llm_service import ILLMService
from ...bedrock_client import BedrockClient
from ..utils import (
    build_prompt_with_context,
    validate_generation_parameters,
    validate_prompt_input,
    format_model_info
)


class BedrockLLMService(ILLMService):
    """
    Bedrock implementation of LLM service.

    Implements: ILLMService (domain contract)
    Uses: LLM utilities from utils module (no inheritance needed)
    """

    def __init__(self, model_id: str, bedrock_client: Optional[BedrockClient] = None):
        """Initialize Bedrock LLM service.

        Accept an optional BedrockClient for easier testing and DI; if none
        provided the service will create one using the shared client class.
        """
        if bedrock_client is None:
            bedrock_client = BedrockClient()
        self.client = bedrock_client
        self.model_id = model_id

    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from Bedrock LLM.

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

            # Run sync Bedrock call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: self.get_completion(
                    prompt=full_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            )
            return response_text

        except Exception as e:
            logger.error(f"Error generating response from Bedrock: {e}")
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
        Generate streaming response from Bedrock LLM.

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
            # TODO: Implement proper streaming with Bedrock streaming API
            response_text = await self.generate_response(
                prompt=prompt,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            yield response_text

        except Exception as e:
            logger.error(f"Error generating streaming response from Bedrock: {e}")
            raise

    def get_provider_name(self) -> str:
        """Get the name of the LLM provider."""
        return "bedrock"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": "bedrock",
            "model_id": self.model_id,
            "region": settings.BEDROCK_REGION
        }

    def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """Get chat completion from Bedrock."""
        try:
            input_data = {
                "messages": messages,
                "temperature": temperature or settings.BEDROCK_TEMPERATURE,
                "max_tokens": max_tokens or settings.BEDROCK_MAX_TOKENS,
                **kwargs
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                input=input_data
            )

            return response.get("completion")

        except Exception as e:
            logger.error(f"Error getting chat completion from Bedrock: {e}")
            raise

    def get_completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """Get text completion from Bedrock."""
        try:
            input_data = {
                "prompt": prompt,
                "temperature": temperature or settings.BEDROCK_TEMPERATURE,
                "max_tokens": max_tokens or settings.BEDROCK_MAX_TOKENS,
                **kwargs
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                input=input_data
            )

            return response.get("completion")

        except Exception as e:
            logger.error(f"Error getting completion from Bedrock: {e}")
            raise
