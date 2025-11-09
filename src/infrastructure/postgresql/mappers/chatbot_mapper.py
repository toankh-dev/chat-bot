"""
Chatbot entity to ORM model mapper.

Handles conversion between domain Chatbot entity and SQLAlchemy Chatbot model.
"""

from typing import Optional
from decimal import Decimal
from domain.entities.chatbot import ChatbotEntity
from domain.value_objects.uuid_vo import UUID as UUIDValue
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
            id=UUIDValue.from_string(str(model.id)),
            workspace_id=UUIDValue.from_string(str(model.created_by)),  # Using created_by as workspace for now
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
    def to_model(entity: ChatbotEntity, created_by: int, existing_model: Optional[ChatbotModel] = None) -> ChatbotModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Chatbot domain entity
            created_by: User ID who created/owns this chatbot
            existing_model: Existing model to update (optional)

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
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model
            return ChatbotModel(
                id=int(str(entity.id).replace('-', '')[:8], 16) % 2147483647,  # Convert UUID to int
                name=entity.name,
                description=entity.description,
                provider="anthropic",  # Default provider
                model=entity.model_id,
                temperature=Decimal(str(entity.temperature)),
                max_tokens=entity.max_tokens,
                top_p=Decimal("1.0"),
                system_prompt=entity.system_prompt,
                max_conversation_length=50,
                enable_function_calling=True,
                api_key_encrypted="",  # Would need to be provided
                created_by=created_by,
                status="active" if entity.is_active else "disabled",
                created_at=entity.created_at,
                updated_at=entity.updated_at
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
