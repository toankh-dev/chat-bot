"""
Chat controller for handling conversational AI interactions.
"""

from fastapi import APIRouter, Depends, HTTPException
from api.middlewares.jwt_middleware import get_current_user
from application.services.chat_service import ChatService
from application.services.conversation_service import ConversationService
from application.services.chatbot_service import ChatbotService
from schemas.chat_schema import ChatRequest, ChatResponse
from core.logger import logger
from core.dependencies import get_conversation_service, get_chatbot_service

router = APIRouter()


def get_chat_service(
    conversation_service: ConversationService = Depends(get_conversation_service),
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
) -> ChatService:
    """Dependency to create ChatService instance."""
    return ChatService(conversation_service, chatbot_service)


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
