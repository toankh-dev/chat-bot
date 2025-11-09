"""
Conversation entity mapper.
"""

from typing import Optional
from domain.entities.conversation import ConversationEntity
from infrastructure.postgresql.models.conversation_model import ConversationModel


class ConversationMapper:
    """Maps between Conversation entity and ConversationModel."""
    
    @staticmethod
    def to_entity(model: ConversationModel) -> ConversationEntity:
        """Convert ConversationModel to Conversation entity."""
        return ConversationEntity(
            id=model.id,
            chatbot_id=model.chatbot_id,
            user_id=model.user_id,
            title=model.title,
            status=model.status,
            is_active=model.is_active,
            started_at=model.started_at,
            last_message_at=model.last_message_at,
            last_accessed_at=model.last_accessed_at,
            message_count=model.message_count
        )
    
    @staticmethod
    def to_model(entity: ConversationEntity) -> ConversationModel:
        """Convert Conversation entity to ConversationModel."""
        return ConversationModel(
            id=entity.id,
            chatbot_id=entity.chatbot_id,
            user_id=entity.user_id,
            title=entity.title,
            status=entity.status,
            is_active=entity.is_active,
            started_at=entity.started_at,
            last_message_at=entity.last_message_at,
            last_accessed_at=entity.last_accessed_at,
            message_count=entity.message_count
        )