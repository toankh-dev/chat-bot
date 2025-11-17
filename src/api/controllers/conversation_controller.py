"""
Conversation controller for handling conversation management.
"""

from fastapi import Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from api.middlewares.jwt_middleware import get_current_user
from schemas.conversation_schema import ConversationResponse, ConversationWithMessagesResponse
from schemas.chat_schema import MessageResponse
from domain.entities.user import UserEntity
from core.dependencies import get_conversation_repository, get_db_session
from shared.interfaces.repositories.conversation_repository import ConversationRepository
from infrastructure.postgresql.models.conversation_model import ConversationModel, MessageModel
from core.logger import logger


async def list_conversations(
    chatbot_id: Optional[int] = Query(None, description="Filter by chatbot ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: UserEntity = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
) -> List[ConversationResponse]:
    """
    List conversations for the current user, optionally filtered by chatbot.

    Args:
        chatbot_id: Optional chatbot ID to filter conversations
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user from JWT
        conversation_repository: Conversation repository instance

    Returns:
        List of conversations

    Raises:
        401: Unauthorized
        500: Server error
    """
    try:
        from infrastructure.postgresql.repositories.conversation_repository import ConversationRepositoryImpl
        
        if isinstance(conversation_repository, ConversationRepositoryImpl):
            repo = conversation_repository
        else:
            from core.dependencies import get_db_session
            async for session in get_db_session():
                repo = ConversationRepositoryImpl(session)
                break
        
        if chatbot_id:
            conversations = await repo.find_by_user_and_chatbot(
                user_id=current_user.id,
                chatbot_id=chatbot_id
            )
        else:
            conversations = await repo.find_by_user(
                user_id=current_user.id,
                skip=skip,
                limit=limit
            )
        
        if not conversations:
            return []
        
        conversation_ids = [conv.id for conv in conversations]
        
        from infrastructure.postgresql.repositories.conversation_repository import ConversationRepositoryImpl
        if isinstance(conversation_repository, ConversationRepositoryImpl):
            session = conversation_repository.session
        else:
            from core.dependencies import get_db_session
            async for session in get_db_session():
                break
        
        count_subquery = (
            select(MessageModel.conversation_id, func.count(MessageModel.id).label('count'))
            .where(MessageModel.conversation_id.in_(conversation_ids))
            .group_by(MessageModel.conversation_id)
            .subquery()
        )
        
        count_result = await session.execute(
            select(count_subquery.c.conversation_id, count_subquery.c.count)
        )
        count_map = {row[0]: row[1] for row in count_result.all()}
        
        result = []
        for conv_model in conversations:
            actual_message_count = count_map.get(conv_model.id, 0)
            
            result.append(ConversationResponse(
                id=conv_model.id,
                chatbot_id=conv_model.chatbot_id,
                user_id=conv_model.user_id,
                title=conv_model.title,
                status=conv_model.status,
                is_active=conv_model.is_active,
                message_count=actual_message_count,
                started_at=conv_model.started_at.isoformat() if conv_model.started_at else "",
                last_message_at=conv_model.last_message_at.isoformat() if conv_model.last_message_at else None,
                last_accessed_at=conv_model.last_accessed_at.isoformat() if conv_model.last_accessed_at else ""
            ))
        
        return result

    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list conversations")


async def get_conversation(
    conversation_id: int,
    current_user: UserEntity = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository)
) -> ConversationWithMessagesResponse:
    """
    Get conversation by ID with all messages.

    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user from JWT
        conversation_repository: Conversation repository instance

    Returns:
        Conversation with messages

    Raises:
        401: Unauthorized
        403: User doesn't own conversation
        404: Conversation not found
        500: Server error
    """
    try:
        from infrastructure.postgresql.repositories.conversation_repository import ConversationRepositoryImpl
        
        if isinstance(conversation_repository, ConversationRepositoryImpl):
            repo = conversation_repository
        else:
            from core.dependencies import get_db_session
            async for session in get_db_session():
                repo = ConversationRepositoryImpl(session)
                break
        
        conv_model = await repo.find_by_id_with_messages(conversation_id)
        
        if not conv_model:
            raise HTTPException(status_code=404, detail=f"Conversation with ID {conversation_id} not found")
        
        if conv_model.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have access to this conversation")
        
        actual_message_count = len(conv_model.messages) if conv_model.messages else conv_model.message_count
        
        conv_response = ConversationResponse(
            id=conv_model.id,
            chatbot_id=conv_model.chatbot_id,
            user_id=conv_model.user_id,
            title=conv_model.title,
            status=conv_model.status,
            is_active=conv_model.is_active,
            message_count=actual_message_count,
            started_at=conv_model.started_at.isoformat() if conv_model.started_at else "",
            last_message_at=conv_model.last_message_at.isoformat() if conv_model.last_message_at else None,
            last_accessed_at=conv_model.last_accessed_at.isoformat() if conv_model.last_accessed_at else ""
        )
        
        messages_response = []
        if conv_model.messages:
            for msg_model in conv_model.messages:
                messages_response.append(MessageResponse(
                    id=msg_model.id,
                    role=msg_model.role,
                    content=msg_model.content,
                    created_at=msg_model.created_at.isoformat() if msg_model.created_at else "",
                    metadata=msg_model.msg_metadata if hasattr(msg_model, 'msg_metadata') and msg_model.msg_metadata else {}
                ))
        
        return ConversationWithMessagesResponse(
            **conv_response.model_dump(),
            messages=messages_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get conversation")

