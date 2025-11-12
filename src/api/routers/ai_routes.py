"""AI routes - Admin-only LLM management and testing endpoints.

Note: Regular users should use /conversations endpoints for chatting.
RAG is now integrated into conversation messages automatically.
"""

from fastapi import APIRouter, Depends, status
from api.controllers.ai_controller import (
    get_available_providers,
    get_ai_system_info,
    test_llm
)
from api.middlewares.jwt_middleware import require_admin

router = APIRouter()

# ============================================================================
# LLM Management Routes (Admin Only)
# ============================================================================

router.add_api_route(
    "/providers",
    get_available_providers,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Get available LLM providers (Admin)",
    description="Get list of available LLM providers and models",
    dependencies=[Depends(require_admin)]
)

router.add_api_route(
    "/info",
    get_ai_system_info,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Get AI system info (Admin)",
    description="Get complete AI system information including RAG and LLM details",
    dependencies=[Depends(require_admin)]
)

router.add_api_route(
    "/test",
    test_llm,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    summary="Test LLM (Admin)",
    description="Test current LLM provider with a sample prompt",
    dependencies=[Depends(require_admin)]
)
