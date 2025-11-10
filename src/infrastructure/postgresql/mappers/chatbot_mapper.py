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
            description=model.description,
            provider=model.provider,
            model=model.model,
            temperature=model.temperature,
            max_tokens=model.max_tokens,
            top_p=model.top_p,
            system_prompt=model.system_prompt,
            welcome_message=model.welcome_message,
            fallback_message=model.fallback_message,
            max_conversation_length=model.max_conversation_length,
            enable_function_calling=model.enable_function_calling,
            api_key_encrypted=model.api_key_encrypted,
            api_base_url=model.api_base_url,
            created_by=model.created_by,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: ChatbotEntity, existing_model: Optional[ChatbotModel] = None) -> ChatbotModel:
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
            existing_model.provider = entity.provider
            existing_model.model = entity.model
            existing_model.temperature = entity.temperature
            existing_model.max_tokens = entity.max_tokens
            existing_model.top_p = entity.top_p
            existing_model.system_prompt = entity.system_prompt
            existing_model.welcome_message = entity.welcome_message
            existing_model.fallback_message = entity.fallback_message
            existing_model.max_conversation_length = entity.max_conversation_length
            existing_model.enable_function_calling = entity.enable_function_calling
            existing_model.api_key_encrypted = entity.api_key_encrypted
            existing_model.api_base_url = entity.api_base_url
            existing_model.status = entity.status
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model
            return ChatbotModel(
                id=entity.id,
                name=entity.name,
                description=entity.description,
                provider=entity.provider,
                model=entity.model,
                temperature=entity.temperature,
                max_tokens=entity.max_tokens,
                top_p=entity.top_p,
                system_prompt=entity.system_prompt,
                welcome_message=entity.welcome_message,
                fallback_message=entity.fallback_message,
                max_conversation_length=entity.max_conversation_length,
                enable_function_calling=entity.enable_function_calling,
                api_key_encrypted=entity.api_key_encrypted,
                api_base_url=entity.api_base_url,
                created_by=entity.created_by,
                status=entity.status,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )

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
            "provider": entity.provider,
            "model": entity.model,
            "temperature": entity.temperature,
            "max_tokens": entity.max_tokens,
            "top_p": entity.top_p,
            "system_prompt": entity.system_prompt,
            "welcome_message": entity.welcome_message,
            "fallback_message": entity.fallback_message,
            "max_conversation_length": entity.max_conversation_length,
            "enable_function_calling": entity.enable_function_calling,
            "api_key_encrypted": entity.api_key_encrypted,
            "api_base_url": entity.api_base_url,
            "created_by": entity.created_by,
            "status": entity.status,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
