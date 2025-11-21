from typing import Any, Optional, Dict, Type
from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from .providers.bedrock_kb import BedrockKnowledgeBaseService
from .providers.gemini_kb import GeminiKnowledgeBaseService
from ..bedrock_client import BedrockClient
from ..gemini_client import GeminiClient

class KnowledgeBaseFactory:
    _providers: Dict[str, Type[IKnowledgeBaseService]] = {
        "bedrock": BedrockKnowledgeBaseService,
        "gemini": GeminiKnowledgeBaseService,
    }

    @classmethod
    def create(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> IKnowledgeBaseService:
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
            return provider_cls(gemini_client=client, vector_store_config=cfg.get("vector_store", {}))

        else:
            raise RuntimeError(f"Provider {provider} not implemented")
