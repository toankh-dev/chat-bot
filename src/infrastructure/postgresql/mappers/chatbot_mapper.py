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
            workspace_id=model.created_by,  # Using created_by as workspace for now
            name=model.name,
            description=model.description or "",
            system_prompt=model.system_prompt or "",
            model_id=model.model,
            temperature=float(model.temperature) if model.temperature else 0.7,
            max_tokens=model.max_tokens or 2048,
            tools=[],  # Tools would need to be loaded from chatbot_tools relationship
            is_active=model.status == "active",
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: ChatbotEntity, created_by: int, existing_model: Optional[ChatbotModel] = None, 
                 provider: str = "anthropic", top_p: Decimal = Decimal("1.0"),
                 welcome_message: Optional[str] = None, fallback_message: Optional[str] = None,
                 max_conversation_length: int = 50, enable_function_calling: bool = True,
                 api_key_encrypted: str = "", api_base_url: Optional[str] = None) -> ChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Chatbot domain entity
            created_by: User ID who created/owns this chatbot
            existing_model: Existing model to update (optional)
            provider: AI provider name (default: anthropic)
            top_p: Top-p sampling parameter
            welcome_message: Welcome message for chatbot
            fallback_message: Fallback message for errors
            max_conversation_length: Maximum conversation length
            enable_function_calling: Whether to enable function calling
            api_key_encrypted: Encrypted API key
            api_base_url: Custom API base URL

        Returns:
            SQLAlchemy Chatbot model
        """
        if existing_model:
            # Update existing model
            existing_model.name = entity.name
            existing_model.description = entity.description
            existing_model.system_prompt = entity.system_prompt
            existing_model.model = entity.model_id
            existing_model.temperature = Decimal(str(entity.temperature))
            existing_model.max_tokens = entity.max_tokens
            existing_model.status = "active" if entity.is_active else "disabled"

            # Update additional fields if provided
            if provider is not None:
                existing_model.provider = provider
            if top_p is not None:
                existing_model.top_p = top_p
            if welcome_message is not None:
                existing_model.welcome_message = welcome_message
            if fallback_message is not None:
                existing_model.fallback_message = fallback_message
            if max_conversation_length is not None:
                existing_model.max_conversation_length = max_conversation_length
            if enable_function_calling is not None:
                existing_model.enable_function_calling = enable_function_calling
            if api_key_encrypted is not None:
                existing_model.api_key_encrypted = api_key_encrypted
            if api_base_url is not None:
                existing_model.api_base_url = api_base_url

            # Remove timezone info for database compatibility
            existing_model.updated_at = entity.updated_at.replace(tzinfo=None) if entity.updated_at and entity.updated_at.tzinfo else entity.updated_at
            return existing_model
        else:
            # Create new model - let database auto-generate the ID
            # Remove timezone info for database compatibility
            created_at = entity.created_at.replace(tzinfo=None) if entity.created_at and entity.created_at.tzinfo else entity.created_at
            updated_at = entity.updated_at.replace(tzinfo=None) if entity.updated_at and entity.updated_at.tzinfo else entity.updated_at
            
            return ChatbotModel(
                name=entity.name,
                description=entity.description,
                provider=provider,
                model=entity.model_id,
                temperature=Decimal(str(entity.temperature)),
                max_tokens=entity.max_tokens,
                top_p=top_p,
                system_prompt=entity.system_prompt,
                welcome_message=welcome_message,
                fallback_message=fallback_message,
                max_conversation_length=max_conversation_length,
                enable_function_calling=enable_function_calling,
                api_key_encrypted=api_key_encrypted,
                api_base_url=api_base_url,
                created_by=created_by,
                status="active" if entity.is_active else "disabled",
                created_at=created_at,
                updated_at=updated_at
            )

    @staticmethod
    def to_model_dict(entity: ChatbotEntity, created_by: int) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: Chatbot domain entity
            created_by: User ID who created this chatbot

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "name": entity.name,
            "description": entity.description,
            "provider": "anthropic",  # Default
            "model": entity.model_id,
            "temperature": Decimal(str(entity.temperature)),
            "max_tokens": entity.max_tokens,
            "system_prompt": entity.system_prompt,
            "status": "active" if entity.is_active else "disabled",
            "created_by": created_by,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
