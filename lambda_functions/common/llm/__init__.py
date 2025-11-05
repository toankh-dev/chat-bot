"""
LLM Provider abstraction layer.
Supports multiple LLM providers: Bedrock (AWS), Gemini (Google), Ollama (local).
"""

from .base import LLMProvider, EmbeddingProvider
from .factory import get_llm_provider, get_embedding_provider
from .providers.bedrock_provider import BedrockLLMProvider, BedrockEmbeddingProvider
from .providers.gemini_provider import GeminiLLMProvider, GeminiEmbeddingProvider

__all__ = [
    'LLMProvider',
    'EmbeddingProvider',
    'get_llm_provider',
    'get_embedding_provider',
    'BedrockLLMProvider',
    'BedrockEmbeddingProvider',
    'GeminiLLMProvider',
    'GeminiEmbeddingProvider',
]
