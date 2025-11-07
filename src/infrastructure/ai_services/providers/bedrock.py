"""
AWS Bedrock LLM provider with integrated client.
Combines Bedrock client and LLM service in one module.
"""

import boto3
import json
from typing import Dict, Any, AsyncGenerator, List, Optional
from botocore.exceptions import ClientError
from infrastructure.ai_services.providers.base import BaseLLMService
from core.config import settings
from core.logger import logger
from core.errors import BedrockError


class BedrockClient:
    """AWS Bedrock client for invoking AI models."""

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
        messages: List[Dict[str, Any]] = None,
        system_prompt: str = None,
        model_id: str = None,
        temperature: float = None,
        max_tokens: int = None,
        body: str = None,  # For direct body input
        **kwargs
    ) -> Dict[str, Any]:
        """Invoke Bedrock model synchronously."""
        try:
            model_id = model_id or settings.BEDROCK_MODEL_ID
            
            # If body is provided directly, use it
            if body:
                request_body = body
            else:
                # Build request body for Claude models
                temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
                max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
                
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": messages or [],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                if system_prompt:
                    request_body["system"] = system_prompt
                
                request_body = json.dumps(request_body)

            logger.info(f"Invoking Bedrock model: {model_id}")

            response = self.runtime_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=request_body
            )

            response_body = json.loads(response['body'].read())
            logger.info(f"Model invocation successful")

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
        messages: List[Dict[str, Any]] = None,
        system_prompt: str = None,
        model_id: str = None,
        temperature: float = None,
        max_tokens: int = None,
        body: str = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Invoke Bedrock model with streaming response."""
        try:
            model_id = model_id or settings.BEDROCK_MODEL_ID
            
            if body:
                request_body = body
            else:
                temperature = temperature if temperature is not None else settings.BEDROCK_TEMPERATURE
                max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS

                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": messages or [],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                if system_prompt:
                    request_body["system"] = system_prompt
                
                request_body = json.dumps(request_body)

            logger.info(f"Starting streaming invocation: {model_id}")

            response = self.runtime_client.invoke_model_with_response_stream(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=request_body
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


class BedrockLLMService(BaseLLMService):
    """AWS Bedrock LLM service implementation."""
    
    def __init__(self, model_id: str = None):
        self.bedrock_client = BedrockClient()
        self.model_id = model_id or settings.BEDROCK_MODEL_ID
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Bedrock."""
        try:
            # Build message format for Claude
            full_prompt = self._build_prompt(prompt, context)
            
            if "claude" in self.model_id.lower():
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                }
                
                response = await self.bedrock_client.invoke_model(
                    model_id=self.model_id,
                    body=json.dumps(body)
                )
                
                return response["content"][0]["text"]
            else:
                # For other models (e.g., Titan, Llama)
                body = {
                    "inputText": full_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "stopSequences": []
                    }
                }
                
                response = await self.bedrock_client.invoke_model(
                    model_id=self.model_id,
                    body=json.dumps(body)
                )
                
                return response["results"][0]["outputText"]
                
        except Exception as e:
            logger.error(f"Bedrock LLM error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_streaming_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ):
        """Generate streaming response using Bedrock."""
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            if "claude" in self.model_id.lower():
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                }
                
                async for chunk in self.bedrock_client.invoke_model_stream(
                    model_id=self.model_id,
                    body=json.dumps(body)
                ):
                    if chunk.get("type") == "content_block_delta":
                        yield chunk["delta"]["text"]
            else:
                body = {
                    "inputText": full_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "stopSequences": []
                    }
                }
                
                async for chunk in self.bedrock_client.invoke_model_stream(
                    model_id=self.model_id,
                    body=json.dumps(body)
                ):
                    yield chunk.get("outputText", "")
                    
        except Exception as e:
            logger.error(f"Bedrock streaming error: {e}")
            raise Exception(f"Failed to generate streaming response: {str(e)}")
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "bedrock"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "bedrock",
            "model_id": self.model_id,
            "supports_streaming": True,
            "supports_context": True
        }
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Build the full prompt with context."""
        if context:
            return f"""Based on the following context, please answer the question.

Context:
{context}

Question: {prompt}

Answer:"""
        return prompt


# Singleton instance
_bedrock_client = None

def get_bedrock_client() -> BedrockClient:
    """Get singleton Bedrock client instance."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client