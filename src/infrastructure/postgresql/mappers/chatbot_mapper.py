"""
Chatbot entity to ORM model mapper.

Handles conversion between domain Chatbot entity and SQLAlchemy Chatbot model.
"""

from domain.entities.chatbot import ChatbotEntity
from infrastructure.postgresql.models import ChatbotModel


class ChatbotMapper:
    """
    Mapper for converting between Chatbot domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: ChatbotModel) -> ChatbotEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy Chatbot model

        Returns:
            Chatbot domain entity
        """
        return ChatbotEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            model=model.model,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            top_p=model.top_p,
            system_prompt=model.system_prompt,
            welcome_message=model.welcome_message,
            fallback_message=model.fallback_message,
            max_conversation_length=model.max_conversation_length,
            enable_function_calling=model.enable_function_calling,
            created_by=model.created_by,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: ChatbotEntity) -> ChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Chatbot domain entity

        Returns:
            SQLAlchemy Chatbot model
        """
        # Create new model - skip id if None to allow auto-generation
        model_data = {
            "name": entity.name,
            "description": entity.description,
            "model": entity.model,
            "temperature": entity.temperature,
            "max_tokens": entity.max_tokens,
            "top_p": entity.top_p,
            "system_prompt": entity.system_prompt,
            "welcome_message": entity.welcome_message,
            "fallback_message": entity.fallback_message,
            "max_conversation_length": entity.max_conversation_length,
            "enable_function_calling": entity.enable_function_calling,
            "created_by": entity.created_by,
            "status": entity.status,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
        # Only set id if entity has a valid id
        if entity.id is not None:
            model_data["id"] = entity.id
        
        return ChatbotModel(**model_data)
