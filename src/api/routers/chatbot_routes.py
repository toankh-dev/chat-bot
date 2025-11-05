"""Chatbot routes."""

from fastapi import APIRouter, status
from typing import List
from src.api.controllers.chatbot_controller import (
    list_chatbots,
    get_chatbot,
    create_chatbot,
    update_chatbot,
    delete_chatbot
)
from src.schemas.chatbot_schema import ChatbotResponse

router = APIRouter()

router.add_api_route(
    "/",
    list_chatbots,
    methods=["GET"],
    response_model=List[ChatbotResponse],
    status_code=status.HTTP_200_OK,
    summary="List chatbots",
    description="List all active chatbots accessible to user"
)

router.add_api_route(
    "/{chatbot_id}",
    get_chatbot,
    methods=["GET"],
    response_model=ChatbotResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chatbot by ID",
    description="Get chatbot details by ID"
)

router.add_api_route(
    "/",
    create_chatbot,
    methods=["POST"],
    response_model=ChatbotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create chatbot",
    description="Create new chatbot (admin only)"
)

router.add_api_route(
    "/{chatbot_id}",
    update_chatbot,
    methods=["PATCH"],
    response_model=ChatbotResponse,
    status_code=status.HTTP_200_OK,
    summary="Update chatbot",
    description="Update chatbot configuration (admin only)"
)

router.add_api_route(
    "/{chatbot_id}",
    delete_chatbot,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chatbot",
    description="Delete chatbot (admin only)"
)
