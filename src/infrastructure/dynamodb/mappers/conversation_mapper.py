"""
Mapper for converting between DynamoDB model/dict and Conversation domain entity.
"""
from src.domain.entities.message import Message
from src.domain.entities.conversation import Conversation as ConversationEntity
from src.infrastructure.dynamodb.models import Conversation as ConversationModel
from typing import Dict, Any

class ConversationMapper:
    @staticmethod
    def to_entity(item: Dict[str, Any]) -> ConversationEntity:
        # Convert DynamoDB dict to Conversation domain entity
        messages = item.get("messages", [])
        message_objs = [Message(**msg) for msg in messages] if messages else []
        return ConversationEntity(
            id=item["id"],
            user_id=item["user_id"],
            chatbot_id=item["chatbot_id"],
            messages=message_objs,
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at")
        )

    @staticmethod
    def to_dict(entity: ConversationModel) -> Dict[str, Any]:
        # Convert Conversation domain entity to dict for DynamoDB
        return {
            "id": entity.id,
            "user_id": entity.user_id,
            "chatbot_id": entity.chatbot_id,
            "messages": [msg.__dict__ for msg in entity.messages],
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }

    @staticmethod
    def to_model(item: Dict[str, Any]) -> ConversationModel:
        # Convert DynamoDB dict to ConversationModel
        return ConversationModel(**item)

    @staticmethod
    def from_model(model: ConversationModel) -> Dict[str, Any]:
        # Convert ConversationModel to dict
        return {
            "id": model.id,
            "user_id": model.user_id,
            "chatbot_id": model.chatbot_id,
            "messages": model.messages,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
