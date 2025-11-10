"""
Factory for creating LLM service instances.
"""
from typing import Optional, Dict, Type, List
from shared.interfaces.services.ai_services.llm_service import ILLMService
from .providers.bedrock_llm import BedrockLLMService
from .providers.gemini_llm import GeminiLLMService
from core.config import settings
from core.logger import logger

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
    def create(cls, config: Optional[dict] = None, **kwargs) -> ILLMService:
        """
        Create LLM service instance based on configured provider.

        Args:
            config: Provider-specific configuration
            **kwargs: Additional provider-specific parameters

        Returns:
            ILLMService: LLM service instance
        """
        provider = settings.LLM_PROVIDER
        if provider not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(cls._providers.keys())}")
            
        provider_cls = cls._providers[provider]
        config = config or {}
        config.update(kwargs)
        
        try:
            if provider == 'bedrock':
                model_id = config.get('model_id', settings.BEDROCK_MODEL_ID)
                if not model_id:
                    raise ValueError("model_id is required for bedrock provider")
                return provider_cls(model_id=model_id)
                
            elif provider == 'gemini':
                api_key = config.get('api_key')
                model_name = config.get('model_name', settings.GEMINI_MODEL)
                if not model_name:
                    raise ValueError("model_name is required for gemini provider")
                return provider_cls(model_name=model_name, api_key=api_key)
                
            else:
                return provider_cls(**config)
                
        except Exception as e:
            raise RuntimeError(f"Failed to create {provider} LLM service: {e}")

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available LLM providers."""
        return ["bedrock", "gemini"]

    @staticmethod
    def get_provider_models() -> Dict[str, List[str]]:
        """Get available models for each provider."""
        return {
            "bedrock": [
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "anthropic.claude-3-opus-20240229-v1:0",
                "amazon.titan-text-premier-v1:0",
                "meta.llama3-70b-instruct-v1:0"
            ],
            "gemini": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ]
        }