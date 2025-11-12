"""AI Controller - Admin-only LLM management and testing endpoints.

Note: User-facing RAG functionality is now integrated into conversation messages.
Regular users chat through /conversations endpoints.
"""

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from core.dependencies import get_rag_service
from shared.interfaces.services.ai_services.rag_service import IRAGService
from infrastructure.ai_services.llm.factory import LLMFactory
from core.logger import logger
from schemas.ai_schema import LLMProvidersResponse, AISystemInfoResponse, LLMTestResponse


# ============================================================================
# Request Models
# ============================================================================

class LLMTestRequest(BaseModel):
    """Request model for LLM testing."""
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7


# ============================================================================
# LLM Management Endpoints
# ============================================================================

async def get_available_providers() -> LLMProvidersResponse:
    """Get list of available LLM providers and models."""
    try:
        providers = LLMFactory.get_available_providers()
        models = LLMFactory.get_provider_models()

        return LLMProvidersResponse(
            providers=providers,
            models=models,
            current_provider="bedrock"  # Default from config
        )
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get providers"
        )


async def get_ai_system_info(
    rag_service: IRAGService = Depends(get_rag_service)
) -> AISystemInfoResponse:
    """Get complete AI system information including RAG and LLM details."""
    try:
        return AISystemInfoResponse(
            ai_system="Unified RAG + LLM System",
            current_llm_provider=rag_service.get_provider_name(),
            model_info=rag_service.get_model_info(),
            knowledge_base="AWS Bedrock Knowledge Base",
            vector_store="S3 + OpenSearch",
            available_endpoints=[
                "/ai/chat - Chat with documents (RAG)",
                "/ai/generate - Direct LLM generation",
                "/ai/search - Semantic search",
                "/ai/contexts - Retrieve contexts only",
                "/ai/providers - Available LLM providers",
                "/ai/test - Test LLM with prompt"
            ]
        )
    except Exception as e:
        logger.error(f"AI system info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI system info"
        )


async def test_llm(
    request: LLMTestRequest,
    rag_service: IRAGService = Depends(get_rag_service)
) -> LLMTestResponse:
    """Test current LLM provider with a sample prompt."""
    try:
        logger.info(f"Testing LLM with prompt: {request.prompt[:50]}...")

        response = await rag_service.generate_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return LLMTestResponse(
            response=response,
            provider=rag_service.get_provider_name(),
            model_info=rag_service.get_model_info(),
            prompt=request.prompt
        )

    except Exception as e:
        logger.error(f"Error testing LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM test failed: {str(e)}"
        )