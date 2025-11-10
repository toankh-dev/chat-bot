"""AI routes - Unified RAG + LLM endpoints."""

from fastapi import APIRouter, status
from api.controllers.ai_controller import (
    get_available_providers,
    get_ai_system_info,
    test_llm,
    generate_text,
    chat_with_documents,
    semantic_search,
    retrieve_contexts
)
from schemas.rag_schema import ChatResponse, SearchResponse, ContextResponse

router = APIRouter()

# ============================================================================
# LLM Management Routes
# ============================================================================

router.add_api_route(
    "/providers",
    get_available_providers,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Get available LLM providers",
    description="Get list of available LLM providers and models"
)

router.add_api_route(
    "/info",
    get_ai_system_info,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Get AI system info",
    description="Get complete AI system information including RAG and LLM details"
)

router.add_api_route(
    "/test",
    test_llm,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    summary="Test LLM",
    description="Test current LLM provider with a sample prompt"
)

router.add_api_route(
    "/generate",
    generate_text,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    summary="Generate text",
    description="Generate text using direct LLM (without RAG)"
)

# ============================================================================
# RAG Routes
# ============================================================================

router.add_api_route(
    "/chat",
    chat_with_documents,
    methods=["POST"],
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with documents",
    description="Chat with documents using RAG (Retrieval-Augmented Generation)"
)

router.add_api_route(
    "/search",
    semantic_search,
    methods=["POST"],
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search",
    description="Perform semantic search across document knowledge base"
)

router.add_api_route(
    "/contexts",
    retrieve_contexts,
    methods=["POST"],
    response_model=ContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve contexts",
    description="Retrieve relevant document contexts without generating response"
)
