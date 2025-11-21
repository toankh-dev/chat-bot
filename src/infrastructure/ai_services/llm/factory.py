"""
Factory for creating LLM service instances.
"""
from typing import Optional, Dict, Type, Any

from shared.interfaces.services.ai_services.llm_service import ILLMService
from infrastructure.ai_services.bedrock_client import BedrockClient
from infrastructure.ai_services.gemini_client import GeminiClient
from .providers.bedrock_llm import BedrockLLMService
from .providers.gemini_llm import GeminiLLMService

class LLMFactory:
    """Factory for creating LLM service instances."""

    _providers: Dict[str, Type[ILLMService]] = {
        'bedrock': BedrockLLMService,
        'gemini': GeminiLLMService,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[ILLMService]):
        """Register a new LLM provider."""
        cls._providers[name] = provider_cls

    @classmethod
    def create(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> ILLMService:
        """
        Create knowledge base service instance using a shared client.

        Args:
            provider: 'bedrock' or 'gemini'
            client: BedrockClient or GeminiClient instance

        Returns:
            IKnowledgeBaseService
        """
        if provider not in cls._providers:
            raise ValueError(f"Unknown knowledge base provider: {provider}. Available: {list(cls._providers.keys())}")

        provider_cls = cls._providers[provider]
        cfg = config or {}
        
        if provider == "bedrock":
            client = BedrockClient.create(cfg)
            return provider_cls(bedrock_client=client)

        elif provider == "gemini":
            client = GeminiClient.create(cfg)
            return provider_cls(gemini_client=client)

        else:
            raise RuntimeError(f"Provider {provider} not implemented")