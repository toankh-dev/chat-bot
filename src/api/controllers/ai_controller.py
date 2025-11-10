"""AI Controller - Unified RAG + LLM endpoints."""

from fastapi import Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel
from schemas.rag_schema import QueryRequest, ChatResponse, SearchResponse, ContextResponse
from usecases.rag_use_cases import ChatWithDocumentsUseCase, SemanticSearchUseCase, RetrieveContextsUseCase
from core.dependencies import (
    get_chat_with_documents_use_case,
    get_semantic_search_use_case,
    get_retrieve_contexts_use_case,
    get_rag_service
)
from shared.interfaces.services.ai_services.rag_service import IRAGService
from infrastructure.ai_services.llm.factory import LLMFactory
from core.logger import logger


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

async def get_available_providers() -> Dict[str, Any]:
    """Get list of available LLM providers and models."""
    try:
        providers = LLMFactory.get_available_providers()
        models = LLMFactory.get_provider_models()

        return {
            "providers": providers,
            "models": models,
            "current_provider": "bedrock"  # Default from config
        }
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get providers"
        )


async def get_ai_system_info(
    rag_service: IRAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """Get complete AI system information including RAG and LLM details."""
    try:
        return {
            "ai_system": "Unified RAG + LLM System",
            "current_llm_provider": rag_service.get_provider_name(),
            "model_info": rag_service.get_model_info(),
            "knowledge_base": "AWS Bedrock Knowledge Base",
            "vector_store": "S3 + OpenSearch",
            "available_endpoints": [
                "/ai/chat - Chat with documents (RAG)",
                "/ai/generate - Direct LLM generation",
                "/ai/search - Semantic search",
                "/ai/contexts - Retrieve contexts only",
                "/ai/providers - Available LLM providers",
                "/ai/test - Test LLM with prompt"
            ]
        }
    except Exception as e:
        logger.error(f"AI system info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI system info"
        )


async def test_llm(
    request: LLMTestRequest,
    rag_service: IRAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """Test current LLM provider with a sample prompt."""
    try:
        logger.info(f"Testing LLM with prompt: {request.prompt[:50]}...")

        response = await rag_service.generate_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return {
            "response": response,
            "provider": rag_service.get_provider_name(),
            "model_info": rag_service.get_model_info(),
            "prompt": request.prompt
        }

    except Exception as e:
        logger.error(f"Error testing LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM test failed: {str(e)}"
        )


async def generate_text(
    request: LLMTestRequest,
    rag_service: IRAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """Generate text using direct LLM (without RAG)."""
    try:
        logger.info(f"Generating text for prompt: {request.prompt[:50]}...")

        response = await rag_service.generate_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return {
            "generated_text": response,
            "provider": rag_service.get_provider_name(),
            "prompt": request.prompt
        }

    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text generation failed: {str(e)}"
        )


# ============================================================================
# RAG Endpoints
# ============================================================================

async def chat_with_documents(
    request: QueryRequest,
    use_case: ChatWithDocumentsUseCase = Depends(get_chat_with_documents_use_case)
) -> ChatResponse:
    """Chat with documents using RAG (Retrieval-Augmented Generation)."""
    try:
        logger.info(f"Processing chat request: {request.query[:50]}...")

        result = await use_case.execute(
            query=request.query,
            domain=request.domain,
            context_limit=request.context_limit
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


async def semantic_search(
    request: QueryRequest,
    use_case: SemanticSearchUseCase = Depends(get_semantic_search_use_case)
) -> SearchResponse:
    """Perform semantic search across document knowledge base."""
    try:
        logger.info(f"Processing search request: {request.query[:50]}...")

        result = await use_case.execute(
            search_query=request.query,
            domain=request.domain,
            result_limit=request.context_limit
        )

        return SearchResponse(**result)

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process search request"
        )


async def retrieve_contexts(
    request: QueryRequest,
    use_case: RetrieveContextsUseCase = Depends(get_retrieve_contexts_use_case)
) -> ContextResponse:
    """Retrieve relevant document contexts without generating response."""
    try:
        logger.info(f"Retrieving contexts for: {request.query[:50]}...")

        contexts = await use_case.execute(
            query=request.query,
            domain=request.domain,
            top_k=request.context_limit
        )

        return ContextResponse(
            contexts=contexts,
            query=request.query,
            domain=request.domain
        )

    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contexts"
        )
