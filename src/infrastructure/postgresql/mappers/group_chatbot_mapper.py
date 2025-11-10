"""
GroupChatbot entity to ORM model mapper.

Handles conversion between domain GroupChatbot entity and SQLAlchemy GroupChatbot model.
"""

from typing import Optional
from domain.entities.group_chatbot import GroupChatbotEntity
from infrastructure.postgresql.models.group_chatbot import GroupChatbotModel


class GroupChatbotMapper:
    """
    Mapper for converting between GroupChatbot domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: GroupChatbotModel) -> GroupChatbotEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy GroupChatbot model

        Returns:
            GroupChatbot domain entity
        """
        return GroupChatbotEntity(
            group_id=model.group_id,
            chatbot_id=model.chatbot_id,
            assigned_by=model.assigned_by,
            created_at=model.assigned_at  # ORM uses assigned_at, entity uses created_at
        )

    @staticmethod
    def to_model(entity: GroupChatbotEntity, existing_model: Optional[GroupChatbotModel] = None) -> GroupChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: GroupChatbot domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy GroupChatbot model
        """
        if existing_model:
            # Update existing model
            existing_model.group_id = entity.group_id
            existing_model.chatbot_id = entity.chatbot_id
            existing_model.assigned_by = entity.assigned_by
            existing_model.assigned_at = entity.created_at
            return existing_model
        else:
            # Create new model
            return GroupChatbotModel(
                group_id=entity.group_id,
                chatbot_id=entity.chatbot_id,
                assigned_by=entity.assigned_by,
                assigned_at=entity.created_at,
                status="active"  # Default status
            )

    @staticmethod
    def to_model_dict(entity: GroupChatbotEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: GroupChatbot domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "group_id": entity.group_id,
            "chatbot_id": entity.chatbot_id,
            "assigned_by": entity.assigned_by,
            "assigned_at": entity.created_at,
            "status": "active"
        }