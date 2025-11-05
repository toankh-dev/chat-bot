"""
Bedrock LLM and Embedding Provider implementation.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from ..base import LLMProvider, EmbeddingProvider, LLMResponse, EmbeddingResponse
from ...config import get_settings, create_client

logger = logging.getLogger(__name__)


class BedrockLLMProvider(LLMProvider):
    """Amazon Bedrock LLM provider implementation."""

    def __init__(self, model_id: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize Bedrock LLM provider.

        Args:
            model_id: Bedrock model ID (defaults to settings)
            region: AWS region (defaults to settings)
        """
        self.settings = get_settings()
        self._model_id = model_id or self.settings.bedrock_model_id
        self._region = region or self.settings.aws_region
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Bedrock client."""
        if self._client is None:
            self._client = create_client('bedrock-runtime', self._region)
            logger.info(f"Initialized Bedrock client for model {self._model_id}")
        return self._client

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def provider_name(self) -> str:
        return "bedrock"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion using Bedrock."""
        # Convert to messages format for chat
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens, temperature, system_prompt=system_prompt, **kwargs)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Multi-turn chat completion using Bedrock."""
        try:
            # Build request body based on model family
            if "anthropic.claude" in self._model_id:
                body = self._build_claude_request(
                    messages, max_tokens, temperature, system_prompt, **kwargs
                )
            elif "amazon.titan" in self._model_id:
                body = self._build_titan_request(
                    messages, max_tokens, temperature, **kwargs
                )
            else:
                raise ValueError(f"Unsupported Bedrock model: {self._model_id}")

            # Invoke model
            response = self.client.invoke_model(
                modelId=self._model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())

            # Extract content based on model family
            if "anthropic.claude" in self._model_id:
                content = response_body['content'][0]['text']
                usage = {
                    'input_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                    'output_tokens': response_body.get('usage', {}).get('output_tokens', 0)
                }
                finish_reason = response_body.get('stop_reason')
            elif "amazon.titan" in self._model_id:
                content = response_body['results'][0]['outputText']
                usage = {
                    'input_tokens': response_body.get('inputTextTokenCount', 0),
                    'output_tokens': response_body.get('results', [{}])[0].get('tokenCount', 0)
                }
                finish_reason = response_body.get('results', [{}])[0].get('completionReason')
            else:
                content = str(response_body)
                usage = None
                finish_reason = None

            return LLMResponse(
                content=content,
                model=self._model_id,
                usage=usage,
                finish_reason=finish_reason,
                metadata=response_body
            )

        except Exception as e:
            logger.error(f"Bedrock LLM error: {e}")
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """Stream text completion using Bedrock."""
        messages = [{"role": "user", "content": prompt}]

        # Build request body
        if "anthropic.claude" in self._model_id:
            body = self._build_claude_request(
                messages, max_tokens, temperature, system_prompt, **kwargs
            )
        elif "amazon.titan" in self._model_id:
            body = self._build_titan_request(
                messages, max_tokens, temperature, **kwargs
            )
        else:
            raise ValueError(f"Unsupported Bedrock model: {self._model_id}")

        # Invoke model with streaming
        response = self.client.invoke_model_with_response_stream(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        # Stream chunks
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'].decode())

            if "anthropic.claude" in self._model_id:
                if chunk.get('type') == 'content_block_delta':
                    yield chunk['delta'].get('text', '')
            elif "amazon.titan" in self._model_id:
                yield chunk.get('outputText', '')

    def _build_claude_request(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request body for Claude models."""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            body["system"] = system_prompt

        # Add optional parameters
        if 'top_p' in kwargs:
            body['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            body['top_k'] = kwargs['top_k']
        if 'stop_sequences' in kwargs:
            body['stop_sequences'] = kwargs['stop_sequences']

        return body

    def _build_titan_request(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Build request body for Titan models."""
        # Titan uses a simpler format - concatenate messages
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": kwargs.get('top_p', 0.9),
            }
        }

        if 'stop_sequences' in kwargs:
            body['textGenerationConfig']['stopSequences'] = kwargs['stop_sequences']

        return body


class BedrockEmbeddingProvider(EmbeddingProvider):
    """Amazon Bedrock Embedding provider implementation."""

    def __init__(self, model_id: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize Bedrock Embedding provider.

        Args:
            model_id: Bedrock embedding model ID (defaults to settings)
            region: AWS region (defaults to settings)
        """
        self.settings = get_settings()
        self._model_id = model_id or self.settings.bedrock_embed_model_id
        self._region = region or self.settings.aws_region
        self._client = None
        self._dimension = self._get_dimension_for_model()

    @property
    def client(self):
        """Lazy initialization of Bedrock client."""
        if self._client is None:
            self._client = create_client('bedrock-runtime', self._region)
            logger.info(f"Initialized Bedrock client for embedding model {self._model_id}")
        return self._client

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def provider_name(self) -> str:
        return "bedrock"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_dimension_for_model(self) -> int:
        """Get embedding dimension based on model ID."""
        if "titan-embed-text-v1" in self._model_id:
            return 1536
        elif "titan-embed-text-v2" in self._model_id:
            return 1024
        elif "cohere.embed" in self._model_id:
            return 1024
        else:
            return 1024  # Default

    def embed_text(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embedding for a single text."""
        try:
            # Build request body based on model family
            if "titan-embed" in self._model_id:
                body = {"inputText": text}
            elif "cohere.embed" in self._model_id:
                body = {"texts": [text], "input_type": "search_document"}
            else:
                body = {"inputText": text}

            # Invoke model
            response = self.client.invoke_model(
                modelId=self._model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())

            # Extract embedding based on model family
            if "titan-embed" in self._model_id:
                embedding = response_body['embedding']
                usage = {'input_tokens': response_body.get('inputTextTokenCount', 0)}
            elif "cohere.embed" in self._model_id:
                embedding = response_body['embeddings'][0]
                usage = None
            else:
                embedding = response_body.get('embedding', [])
                usage = None

            return EmbeddingResponse(
                embedding=embedding,
                model=self._model_id,
                usage=usage,
                metadata=response_body
            )

        except Exception as e:
            logger.error(f"Bedrock embedding error: {e}")
            raise

    def embed_batch(self, texts: List[str], **kwargs) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts."""
        # Bedrock doesn't support batch embeddings natively for all models
        # Process sequentially
        return [self.embed_text(text, **kwargs) for text in texts]
