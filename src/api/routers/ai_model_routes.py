"""AI Model routes."""

from fastapi import APIRouter, status
from typing import List
from api.controllers.ai_model_controller import (
    list_ai_models,
    get_ai_model,
    create_ai_model,
    update_ai_model,
    delete_ai_model
)
from schemas.ai_model_schema import AiModelResponse

router = APIRouter()

router.add_api_route(
    "/",
    list_ai_models,
    methods=["GET"],
    response_model=List[AiModelResponse],
    status_code=status.HTTP_200_OK,
    summary="List AI models",
    description="List all available AI models"
)

router.add_api_route(
    "/{model_id}",
    get_ai_model,
    methods=["GET"],
    response_model=AiModelResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI model by ID",
    description="Get AI model details by ID"
)

router.add_api_route(
    "/",
    create_ai_model,
    methods=["POST"],
    response_model=AiModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI model",
    description="Create new AI model (admin only)"
)

router.add_api_route(
    "/{model_id}",
    update_ai_model,
    methods=["PATCH"],
    response_model=AiModelResponse,
    status_code=status.HTTP_200_OK,
    summary="Update AI model",
    description="Update AI model information (admin only)"
)

router.add_api_route(
    "/{model_id}",
    delete_ai_model,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete AI model",
    description="Delete AI model (admin only)"
)

