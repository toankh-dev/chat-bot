"""
AI Services Factory for creating provider instances.
"""

from typing import Optional
from infrastructure.ai_services.providers.base import BaseLLMService
from infrastructure.ai_services.providers.bedrock import BedrockLLMService
from infrastructure.ai_services.providers.gemini import GeminiLLMService
from core.config import settings
from core.logger import logger

class LLMFactory:
    """Factory for creating LLM service instances."""
    
    @staticmethod
    def create(
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs
    ) -> BaseLLMService:
        """
        Create LLM service instance based on provider.
        
        Args:
            provider: LLM provider ('bedrock', 'gemini')
            model_id: Specific model ID/name
            **kwargs: Additional provider-specific parameters
            
        Returns:
            BaseLLMService: LLM service instance
        """
        provider = provider or settings.LLM_PROVIDER
        
        logger.info(f"Creating LLM service: {provider}")
        
        if provider.lower() == "bedrock":
            return BedrockLLMService(
                model_id=model_id or settings.BEDROCK_MODEL_ID
            )
        
        elif provider.lower() == "gemini":
            return GeminiLLMService(
                api_key=kwargs.get('api_key'),
                model_name=model_id or settings.GEMINI_MODEL_NAME
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available LLM providers."""
        return ["bedrock", "gemini"]
    
    @staticmethod
    def get_provider_models() -> dict[str, list[str]]:
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