"""
Amazon Bedrock Client
Wrapper for Bedrock LLM and Embedding models
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for Amazon Bedrock LLM and Embeddings"""

    def __init__(
        self,
        region: str = None,
        llm_model_id: str = None,
        embed_model_id: str = None
    ):
        """
        Initialize Bedrock client

        Args:
            region: AWS region
            llm_model_id: LLM model ID (e.g., anthropic.claude-3-5-sonnet)
            embed_model_id: Embedding model ID (e.g., amazon.titan-embed-text-v2)
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.llm_model_id = llm_model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        self.embed_model_id = embed_model_id or os.getenv(
            "BEDROCK_EMBED_MODEL_ID",
            "amazon.titan-embed-text-v2:0"
        )

        # Initialize Bedrock client with retry config
        config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=30,
            read_timeout=300
        )

        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            config=config
        )

        logger.info(f"Initialized Bedrock client in {self.region}")
        logger.info(f"LLM Model: {self.llm_model_id}")
        logger.info(f"Embedding Model: {self.embed_model_id}")

    def invoke_llm(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> str:
        """
        Invoke Bedrock LLM

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Top-p sampling
            stop_sequences: Stop sequences
            system_prompt: System prompt
            model_id: Override default model ID

        Returns:
            Generated text
        """
        model = model_id or self.llm_model_id

        try:
            # Build request body based on model family
            if "anthropic.claude" in model:
                body = self._build_claude_request(
                    prompt, max_tokens, temperature, top_p,
                    stop_sequences, system_prompt
                )
            elif "amazon.titan" in model:
                body = self._build_titan_request(
                    prompt, max_tokens, temperature, top_p, stop_sequences
                )
            elif "meta.llama" in model:
                body = self._build_llama_request(
                    prompt, max_tokens, temperature, top_p
                )
            else:
                raise ValueError(f"Unsupported model: {model}")

            logger.debug(f"Invoking {model} with prompt length: {len(prompt)}")

            # Invoke model
            response = self.bedrock_runtime.invoke_model(
                modelId=model,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            generated_text = self._extract_text_from_response(
                response_body, model
            )

            logger.info(f"Generated {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Error invoking Bedrock LLM: {e}")
            raise

    def invoke_llm_streaming(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        """
        Invoke Bedrock LLM with streaming response

        Args:
            Same as invoke_llm

        Yields:
            Text chunks as they are generated
        """
        model = model_id or self.llm_model_id

        try:
            # Build request body
            if "anthropic.claude" in model:
                body = self._build_claude_request(
                    prompt, max_tokens, temperature, top_p,
                    stop_sequences, system_prompt
                )
            else:
                # Fallback to non-streaming
                yield self.invoke_llm(
                    prompt, max_tokens, temperature, top_p,
                    stop_sequences, system_prompt, model_id
                )
                return

            # Invoke with streaming
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=model,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )

            # Stream response
            for event in response['body']:
                if 'chunk' in event:
                    chunk = json.loads(event['chunk']['bytes'])
                    if 'delta' in chunk:
                        if 'text' in chunk['delta']:
                            yield chunk['delta']['text']

        except Exception as e:
            logger.error(f"Error in streaming LLM: {e}")
            raise

    def generate_embeddings(
        self,
        texts: List[str],
        model_id: Optional[str] = None,
        normalize: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings using Bedrock

        Args:
            texts: List of texts to embed
            model_id: Override default embedding model
            normalize: Normalize embeddings

        Returns:
            List of embedding vectors
        """
        model = model_id or self.embed_model_id
        embeddings = []

        try:
            for text in texts:
                # Build request based on model
                if "amazon.titan-embed" in model:
                    body = {
                        "inputText": text,
                        "normalize": normalize
                    }
                elif "cohere.embed" in model:
                    body = {
                        "texts": [text],
                        "input_type": "search_document"
                    }
                else:
                    raise ValueError(f"Unsupported embedding model: {model}")

                # Invoke model
                response = self.bedrock_runtime.invoke_model(
                    modelId=model,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )

                # Parse response
                response_body = json.loads(response['body'].read())

                if "amazon.titan-embed" in model:
                    embedding = response_body.get('embedding', [])
                elif "cohere.embed" in model:
                    embedding = response_body.get('embeddings', [[]])[0]
                else:
                    embedding = []

                embeddings.append(embedding)

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def _build_claude_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop_sequences: Optional[List[str]],
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Build request body for Claude models"""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        if system_prompt:
            body["system"] = system_prompt

        if stop_sequences:
            body["stop_sequences"] = stop_sequences

        return body

    def _build_titan_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop_sequences: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build request body for Titan models"""
        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": top_p
            }
        }

        if stop_sequences:
            body["textGenerationConfig"]["stopSequences"] = stop_sequences

        return body

    def _build_llama_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> Dict[str, Any]:
        """Build request body for Llama models"""
        return {
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

    def _extract_text_from_response(
        self,
        response: Dict[str, Any],
        model_id: str
    ) -> str:
        """Extract generated text from response based on model"""
        if "anthropic.claude" in model_id:
            # Claude response format
            content = response.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return ''

        elif "amazon.titan" in model_id:
            # Titan response format
            results = response.get('results', [])
            if results and len(results) > 0:
                return results[0].get('outputText', '')
            return ''

        elif "meta.llama" in model_id:
            # Llama response format
            return response.get('generation', '')

        else:
            # Fallback
            return str(response)


class BedrockAgentClient:
    """Client for Bedrock Agents (alternative to LangChain orchestrator)"""

    def __init__(self, region: str = None):
        """Initialize Bedrock Agents client"""
        self.region = region or os.getenv("AWS_REGION", "us-east-1")

        config = Config(
            region_name=self.region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            config=config
        )

        logger.info("Initialized Bedrock Agent client")

    def invoke_agent(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent

        Args:
            agent_id: Agent ID
            agent_alias_id: Agent alias ID
            session_id: Session ID for conversation
            input_text: User input
            enable_trace: Enable trace output

        Returns:
            Agent response
        """
        try:
            response = self.bedrock_agent.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=enable_trace
            )

            # Process completion stream
            completion = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')

            return {
                "completion": completion,
                "session_id": session_id,
                "trace": response.get('trace') if enable_trace else None
            }

        except Exception as e:
            logger.error(f"Error invoking Bedrock Agent: {e}")
            raise
