"""
AWS Bedrock client for AI model interactions.
"""

import boto3
import json
from typing import Dict, Any, AsyncGenerator, List
from botocore.exceptions import ClientError
from src.core.config import settings
from src.core.logger import logger
from src.core.errors import BedrockError


class BedrockClient:
    """
    AWS Bedrock client for invoking AI models.

    Supports both synchronous and streaming responses.
    """

    def __init__(self):
        """Initialize Bedrock client."""
        self._client = None
        self._runtime_client = None

    @property
    def client(self):
        """Get or create Bedrock client."""
        if self._client is None:
            self._client = boto3.client(
                'bedrock',
                region_name=settings.BEDROCK_REGION
            )
        return self._client

    @property
    def runtime_client(self):
        """Get or create Bedrock Runtime client."""
        if self._runtime_client is None:
            self._runtime_client = boto3.client(
                'bedrock-runtime',
                region_name=settings.BEDROCK_REGION
            )
        return self._runtime_client

    async def invoke_model(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = None,
        model_id: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model synchronously.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            model_id: Model identifier (defaults to config)
            temperature: Model temperature (defaults to config)
            max_tokens: Maximum tokens (defaults to config)
            tools: Optional tool definitions

        Returns:
            Model response dictionary

        Raises:
            BedrockError: If the invocation fails
        """
        try:
            model_id = model_id or settings.BEDROCK_MODEL_ID
            temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
            max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS

            # Build request body for Claude models
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            if system_prompt:
                request_body["system"] = system_prompt

            if tools:
                request_body["tools"] = tools

            logger.info(f"Invoking Bedrock model: {model_id}")

            response = self.runtime_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            logger.info(f"Model invocation successful. Stop reason: {response_body.get('stop_reason')}")

            return response_body

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock invocation failed: {error_code} - {error_message}")
            raise BedrockError(
                message=f"Model invocation failed: {error_message}",
                details={"error_code": error_code, "model_id": model_id}
            )
        except Exception as e:
            logger.error(f"Unexpected error during Bedrock invocation: {str(e)}")
            raise BedrockError(
                message=f"Unexpected error: {str(e)}",
                details={"model_id": model_id}
            )

    async def invoke_model_stream(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = None,
        model_id: str = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Invoke Bedrock model with streaming response.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            model_id: Model identifier
            temperature: Model temperature
            max_tokens: Maximum tokens
            tools: Optional tool definitions

        Yields:
            Streaming response chunks

        Raises:
            BedrockError: If the invocation fails
        """
        try:
            model_id = model_id or settings.BEDROCK_MODEL_ID
            temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
            max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS

            # Build request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            if system_prompt:
                request_body["system"] = system_prompt

            if tools:
                request_body["tools"] = tools

            logger.info(f"Starting streaming invocation: {model_id}")

            response = self.runtime_client.invoke_model_with_response_stream(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )

            # Process streaming response
            stream = response['body']
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_data = json.loads(chunk['bytes'].decode())
                    yield chunk_data

            logger.info("Streaming invocation completed")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock streaming failed: {error_code} - {error_message}")
            raise BedrockError(
                message=f"Streaming invocation failed: {error_message}",
                details={"error_code": error_code, "model_id": model_id}
            )
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {str(e)}")
            raise BedrockError(
                message=f"Unexpected streaming error: {str(e)}",
                details={"model_id": model_id}
            )

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available Bedrock models.

        Returns:
            List of available model information
        """
        try:
            response = self.client.list_foundation_models()
            models = response.get('modelSummaries', [])

            logger.info(f"Found {len(models)} available models")
            return models

        except ClientError as e:
            logger.error(f"Failed to list models: {str(e)}")
            raise BedrockError(
                message="Failed to list available models",
                details={"error": str(e)}
            )


# Singleton instance
_bedrock_client = None


def get_bedrock_client() -> BedrockClient:
    """Get singleton Bedrock client instance."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
