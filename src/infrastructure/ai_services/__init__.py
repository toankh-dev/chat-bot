"""
AI Services - LLM, Embeddings, and Knowledge Base providers.

Clean architecture:
- llm/: Large Language Model services (Bedrock, Gemini)
- embeddings/: Text embedding services (Bedrock, Gemini)
- knowledge_base/: Knowledge Base services for RAG

Design principles:
- Domain interfaces (IEmbeddingService, ILLMService) define contracts
- Utility modules provide shared functions (no inheritance needed)
- Provider implementations use single inheritance
"""

# LLM
from infrastructure.ai_services.llm import (
    BedrockLLMService,
    GeminiLLMService,
    LLMFactory
)

# Embeddings
from infrastructure.ai_services.embeddings import (
    BedrockEmbeddingService,
    GeminiEmbeddingService,
    EmbeddingFactory
)

# Knowledge Base
from infrastructure.ai_services.knowledge_base import BedrockKnowledgeBaseService

# Bedrock Client (shared across services) - optional
try:
    from infrastructure.ai_services.bedrock_client import BedrockClient, get_bedrock_client
except ImportError:
    BedrockClient = None
    get_bedrock_client = None

__all__ = [
    # LLM
    "BedrockLLMService",
    "GeminiLLMService",
    "LLMFactory",

    # Embeddings
    "BedrockEmbeddingService",
    "GeminiEmbeddingService",
    "EmbeddingFactory",

    # Knowledge Base
    "BedrockKnowledgeBaseService",

    # Bedrock Client
    "BedrockClient",
    "get_bedrock_client"
]
