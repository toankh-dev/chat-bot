"""
Conversation Management API
"""

import sys
import os
from fastapi import Depends, Query
from typing import Optional

# Add paths
sys.path.insert(0, '/opt/python')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))

# Import shared base
from utils.fastapi_base import create_management_app

# Import services and models
from common.services.conversation_service import ConversationService
from common.models.api.conversation_models import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    conversation_to_response
)
from common.auth.jwt import require_auth, get_current_user

# Create app
app = create_management_app(
    title="Conversation Management API",
    description="Manage conversations and chat history",
    version="2.0.0"
)

# Initialize service
conversation_service = ConversationService()


# ==============================================================================
# Conversation Routes
# ==============================================================================

@app.get("/conversations", tags=["Conversations"])
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = None,
    current_user: dict = Depends(require_auth)
):
    """
    List conversations with pagination

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10, max: 100)
    - **user_id**: Filter by user ID (optional, admin only)
    """
    # If user_id not specified, show current user's conversations
    if user_id is None:
        user_id = current_user.get('user_id')
    elif user_id != current_user.get('user_id'):
        # Check if user is admin (for viewing other users' conversations)
        if not current_user.get('is_admin'):
            raise HTTPException(status_code=403, detail="Access denied")

    conversations, total = conversation_service.list_conversations(
        user_id=user_id,
        page=page,
        limit=limit
    )

    return {
        "data": [conversation_to_response(conv) for conv in conversations],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.post("/conversations", tags=["Conversations"], status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(require_auth)
):
    """Create a new conversation"""
    conversation = conversation_service.create_conversation(
        user_id=current_user.get('user_id'),
        title=request.title,
        metadata=request.metadata
    )

    return {
        "message": "Conversation created successfully",
        "data": conversation_to_response(conversation)
    }


@app.get("/conversations/{conversation_id}", tags=["Conversations"])
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_auth)
):
    """Get conversation by ID"""
    conversation = conversation_service.get_conversation(conversation_id)

    # Check ownership
    if conversation.user_id != current_user.get('user_id') and not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Access denied")

    return {"data": conversation_to_response(conversation)}


@app.put("/conversations/{conversation_id}", tags=["Conversations"])
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: dict = Depends(require_auth)
):
    """Update conversation"""
    conversation = conversation_service.get_conversation(conversation_id)

    # Check ownership
    if conversation.user_id != current_user.get('user_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    updated = conversation_service.update_conversation(
        conversation_id=conversation_id,
        title=request.title,
        metadata=request.metadata
    )

    return {
        "message": "Conversation updated successfully",
        "data": conversation_to_response(updated)
    }


@app.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_auth)
):
    """Delete conversation"""
    conversation = conversation_service.get_conversation(conversation_id)

    # Check ownership
    if conversation.user_id != current_user.get('user_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    conversation_service.delete_conversation(conversation_id)

    return {"message": "Conversation deleted successfully"}


# ==============================================================================
# Messages Routes
# ==============================================================================

@app.get("/conversations/{conversation_id}/messages", tags=["Messages"])
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_auth)
):
    """Get messages in a conversation"""
    conversation = conversation_service.get_conversation(conversation_id)

    # Check ownership
    if conversation.user_id != current_user.get('user_id') and not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Access denied")

    messages, total = conversation_service.get_messages(
        conversation_id=conversation_id,
        page=page,
        limit=limit
    )

    return {
        "data": messages,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.post("/conversations/{conversation_id}/messages", tags=["Messages"])
async def add_message(
    conversation_id: str,
    message: dict,
    current_user: dict = Depends(require_auth)
):
    """Add a message to conversation"""
    conversation = conversation_service.get_conversation(conversation_id)

    # Check ownership
    if conversation.user_id != current_user.get('user_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    result = conversation_service.add_message(
        conversation_id=conversation_id,
        role=message.get('role'),
        content=message.get('content'),
        metadata=message.get('metadata')
    )

    return {
        "message": "Message added successfully",
        "data": result
    }


# ==============================================================================
# Statistics
# ==============================================================================

@app.get("/conversations/stats/summary", tags=["Statistics"])
async def get_conversation_stats(current_user: dict = Depends(get_current_user)):
    """Get conversation statistics for current user"""
    stats = conversation_service.get_user_stats(current_user.get('user_id'))

    return {"data": stats}
