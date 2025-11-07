"""Conversation routes."""

from fastapi import APIRouter, status
from typing import List
from api.controllers.conversation_controller import (
    list_conversations,
    get_conversation,
    create_conversation,
    create_message,
    delete_conversation
)
from schemas.conversation_schema import (
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse
)

router = APIRouter()

router.add_api_route(
    "/",
    list_conversations,
    methods=["GET"],
    response_model=List[ConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="List user's conversations"
)

router.add_api_route(
    "/{conversation_id}",
    get_conversation,
    methods=["GET"],
    response_model=ConversationWithMessages,
    status_code=status.HTTP_200_OK,
    summary="Get conversation",
    description="Get conversation with all messages"
)

router.add_api_route(
    "/",
    create_conversation,
    methods=["POST"],
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create new conversation with chatbot"
)

router.add_api_route(
    "/{conversation_id}/messages",
    create_message,
    methods=["POST"],
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create message",
    description="Create new message in conversation"
)

router.add_api_route(
    "/{conversation_id}",
    delete_conversation,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete conversation and all messages"
)
