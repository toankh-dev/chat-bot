"""
UserChatbot entity to ORM model mapper.

Handles conversion between domain UserChatbot entity and SQLAlchemy UserChatbot model.
"""

from typing import Optional
from domain.entities.user_chatbot import UserChatbotEntity
from infrastructure.postgresql.models.user_chatbot import UserChatbotModel


class UserChatbotMapper:
    """
    Mapper for converting between UserChatbot domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: UserChatbotModel) -> UserChatbotEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy UserChatbot model

        Returns:
            UserChatbot domain entity
        """
        return UserChatbotEntity(
            user_id=model.user_id,
            chatbot_id=model.chatbot_id,
            assigned_by=model.assigned_by,
            created_at=model.assigned_at  # ORM uses assigned_at, entity uses created_at
        )

    @staticmethod
    def to_model(entity: UserChatbotEntity, existing_model: Optional[UserChatbotModel] = None) -> UserChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: UserChatbot domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy UserChatbot model
        """
        if existing_model:
            # Update existing model
            existing_model.user_id = entity.user_id
            existing_model.chatbot_id = entity.chatbot_id
            existing_model.assigned_by = entity.assigned_by
            existing_model.assigned_at = entity.created_at
            return existing_model
        else:
            # Create new model
            return UserChatbotModel(
                user_id=entity.user_id,
                chatbot_id=entity.chatbot_id,
                assigned_by=entity.assigned_by,
                assigned_at=entity.created_at,
                status="active"  # Default status
            )

    @staticmethod
    def to_model_dict(entity: UserChatbotEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: UserChatbot domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "user_id": entity.user_id,
            "chatbot_id": entity.chatbot_id,
            "assigned_by": entity.assigned_by,
            "assigned_at": entity.created_at,
            "status": "active"
        }