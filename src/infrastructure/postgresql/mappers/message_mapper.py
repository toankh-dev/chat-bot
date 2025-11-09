"""
Message entity mapper.
"""

from typing import Optional
from domain.entities.message import MessageEntity
from infrastructure.postgresql.models.conversation_model import MessageModel


class MessageMapper:
    """Maps between Message entity and MessageModel."""
    
    @staticmethod
    def to_entity(model: MessageModel) -> MessageEntity:
        """Convert MessageModel to Message entity."""
        return MessageEntity(
            id=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            message_metadata=model.message_metadata,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: MessageEntity) -> MessageModel:
        """Convert Message entity to MessageModel."""
        return MessageModel(
            id=entity.id,
            conversation_id=entity.conversation_id,
            role=entity.role,
            content=entity.content,
            message_metadata=entity.message_metadata,
            created_at=entity.created_at
        )