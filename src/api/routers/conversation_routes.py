"""Conversation routes."""

from fastapi import APIRouter, status
from typing import List
from api.controllers.conversation_controller import (
    list_conversations,
    get_conversation
)
from schemas.conversation_schema import ConversationResponse, ConversationWithMessagesResponse

router = APIRouter()

router.add_api_route(
    "/",
    list_conversations,
    methods=["GET"],
    response_model=List[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="List conversations for the current user, optionally filtered by chatbot"
)

router.add_api_route(
    "/{conversation_id}",
    get_conversation,
    methods=["GET"],
    response_model=ConversationWithMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation",
    description="Get conversation by ID with all messages"
)

