"""
Chatbot entity to ORM model mapper.

Handles conversion between domain Chatbot entity and SQLAlchemy Chatbot model.
"""

from typing import Optional
from decimal import Decimal
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
            description=model.description or "",
            model_id=model.model_id,
            temperature=float(model.temperature) if model.temperature else 0.7,
            max_tokens=model.max_tokens or 2048,
            top_p=float(model.top_p) if model.top_p else 1.0,
            system_prompt=model.system_prompt or "",
            welcome_message=model.welcome_message or "",
            fallback_message=model.fallback_message or "",
            max_conversation_length=model.max_conversation_length or 50,
            enable_function_calling=model.enable_function_calling if model.enable_function_calling is not None else True,
            created_by=model.created_by,
            status=model.status or "active",
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(
        entity: ChatbotEntity, 
        existing_model: Optional[ChatbotModel] = None,
        created_by: Optional[int] = None,
        model_id: Optional[int] = None,
        top_p: Optional[Decimal] = None,
        welcome_message: Optional[str] = None,
        fallback_message: Optional[str] = None,
        max_conversation_length: Optional[int] = None,
        enable_function_calling: Optional[bool] = None
    ) -> ChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Chatbot domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy Chatbot model
        """
        if existing_model:
            # Update existing model
            existing_model.name = entity.name
            existing_model.description = entity.description
            existing_model.model_id = entity.model_id
            existing_model.temperature = Decimal(str(entity.temperature))
            existing_model.max_tokens = entity.max_tokens
            existing_model.top_p = Decimal(str(entity.top_p))
            existing_model.system_prompt = entity.system_prompt
            existing_model.welcome_message = entity.welcome_message
            existing_model.fallback_message = entity.fallback_message
            existing_model.max_conversation_length = entity.max_conversation_length
            existing_model.enable_function_calling = entity.enable_function_calling
            existing_model.created_by = entity.created_by
            existing_model.status = entity.status
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model - skip id if None to allow auto-generation
            # Use provided parameters if available, otherwise use entity values
            model_data = {
                "name": entity.name,
                "description": entity.description,
                "model_id": model_id if model_id is not None else entity.model_id,
                "temperature": Decimal(str(entity.temperature)),
                "max_tokens": entity.max_tokens,
                "top_p": Decimal(str(top_p)) if top_p is not None else Decimal(str(entity.top_p)),
                "system_prompt": entity.system_prompt,
                "welcome_message": welcome_message if welcome_message is not None else entity.welcome_message,
                "fallback_message": fallback_message if fallback_message is not None else entity.fallback_message,
                "max_conversation_length": max_conversation_length if max_conversation_length is not None else entity.max_conversation_length,
                "enable_function_calling": enable_function_calling if enable_function_calling is not None else entity.enable_function_calling,
                "created_by": created_by if created_by is not None else entity.created_by,
                "status": entity.status,
                "created_at": entity.created_at.replace(tzinfo=None) if entity.created_at and entity.created_at.tzinfo else entity.created_at,
                "updated_at": entity.updated_at.replace(tzinfo=None) if entity.updated_at and entity.updated_at.tzinfo else entity.updated_at
            }
            # Only set id if entity has a valid positive id (not 0 or None)
            # This allows the database to auto-generate the ID for new entities
            if entity.id is not None and entity.id > 0:
                model_data["id"] = entity.id

            return ChatbotModel(**model_data)

    @staticmethod
    def to_model_dict(entity: ChatbotEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: Chatbot domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "name": entity.name,
            "description": entity.description,
            "model_id": entity.model_id,
            "temperature": Decimal(str(entity.temperature)),
            "max_tokens": entity.max_tokens,
            "top_p": Decimal(str(entity.top_p)),
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
