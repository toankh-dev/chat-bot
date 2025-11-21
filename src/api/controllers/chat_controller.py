"""
Chat controller for handling conversational AI interactions.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.middlewares.jwt_middleware import get_current_user
from application.services.chat_service import ChatService
from application.services.conversation_service import ConversationService
from application.services.chatbot_service import ChatbotService
from schemas.chat_schema import ChatRequest, ChatResponse
from api.schemas.streaming_schemas import ChatStreamRequest
from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from shared.interfaces.repositories.knowledge_base_repository import IKnowledgeBaseRepository
from infrastructure.vector_store.factory import IVectorStoreFactory
from core.logger import logger
from core.dependencies import (
    get_conversation_service,
    get_chatbot_service,
    get_embedding_service,
    get_vector_store_factory,
    get_knowledge_base_sync_repository
)
import json

from src.shared.utils.common import to_serializable

router = APIRouter()


def get_chat_service(
    conversation_service: ConversationService = Depends(get_conversation_service),
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
    embedding_service: IEmbeddingService = Depends(get_embedding_service),
    vector_store_factory: IVectorStoreFactory = Depends(get_vector_store_factory),
    knowledge_base_repository: IKnowledgeBaseRepository = Depends(get_knowledge_base_sync_repository)
) -> ChatService:
    """Dependency to create ChatService instance with RAG support."""
    return ChatService(
        conversation_service,
        chatbot_service,
        embedding_service,
        vector_store_factory,
        knowledge_base_repository
    )


@router.post("/chatbots/{bot_id}/chat", response_model=ChatResponse, tags=["Chat"])
async def send_message(
    bot_id: int,
    request: ChatRequest,
    current_user=Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to a chatbot and get AI response.

    Args:
        bot_id: Chatbot ID
        request: Chat request with message and optional conversation_id
        current_user: Authenticated user from JWT
        chat_service: Chat service instance

    Returns:
        ChatResponse with user and assistant messages

    Raises:
        400: Invalid input
        401: Unauthorized
        403: User doesn't own conversation
        404: Chatbot not found or inactive
        500: AI service error
    """
    try:
        response = await chat_service.send_message_and_get_response(
            bot_id=bot_id,
            user_id=current_user.id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        return response

    except ValueError as e:
        logger.error(f"Validation error in chat: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except PermissionError as e:
        logger.error(f"Permission error in chat: {e}")
        raise HTTPException(status_code=403, detail="You don't have access to this conversation")

    except TimeoutError as e:
        logger.error(f"Timeout error in chat: {e}")
        raise HTTPException(status_code=504, detail=str(e))

    except ConnectionError as e:
        logger.error(f"Connection error in chat: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        error_message = str(e) if str(e) else "Failed to process chat message. Please try again."
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/chatbots/{bot_id}/chat/stream", tags=["Chat"])
async def send_message_stream(
    bot_id: int,
    request: ChatStreamRequest,
    current_user=Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Send message and receive streaming response (Server-Sent Events).

    This endpoint provides real-time streaming of AI responses, including:
    - Token-by-token text generation
    - Agent tool execution events
    - Progress updates

    Args:
        bot_id: Chatbot ID
        request: Streaming chat request with message and optional conversation_id
        current_user: Authenticated user from JWT
        chat_service: Chat service instance
        agent_service: Agent service instance (for agent-enabled chatbots)

    Returns:
        StreamingResponse with Server-Sent Events

    Response format:
        Content-Type: text/event-stream

        Event types:
        - start: Stream started with conversation info
        - token: Text token from AI response
        - tool_start: Agent started using a tool
        - tool_end: Tool execution completed
        - agent_select: Agent was selected by orchestrator
        - info: Informational message
        - done: Stream completed
        - error: Error occurred
    """
    async def event_generator():
        """Generate SSE events from chat service."""
        try:
            logger.info(f"Starting streaming chat for bot {bot_id}, user {current_user.id}")

            # Stream from chat service
            async for event in chat_service.send_message_and_stream_response(
                bot_id=bot_id,
                user_id=current_user.id,
                message=request.message,
                conversation_id=request.conversation_id,
            ):
                # Format as Server-Sent Events
                event_type = event.get("type", "message")
                event_data = event.get("data", {})

                try:
                    data_json = json.dumps(event_data, default=to_serializable, ensure_ascii=False)
                except TypeError:
                    data_json = json.dumps(str(event_data), ensure_ascii=False)
                
                # SSE format: "event: type\ndata: {...}\n\n"
                yield f"event: {event_type}\n"
                yield f"data: {data_json}\n\n"

                # Check for error events
                if event_type == "error":
                    logger.error(f"Error in stream: {event_data}")
                    break

        except Exception as e:
            logger.error(f"Streaming error in controller: {e}", exc_info=True)
            # Send error event
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e), 'message': 'Streaming failed'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for real-time streaming
            "Access-Control-Allow-Origin": "*",  # Allow CORS for streaming
        }
    )
