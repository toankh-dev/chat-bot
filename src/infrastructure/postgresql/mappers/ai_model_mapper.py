"""
AI Model entity to ORM model mapper.

Handles conversion between domain AiModel entity and SQLAlchemy AiModel model.
"""

from typing import Optional
from domain.entities.ai_model import AiModelEntity
from infrastructure.postgresql.models.ai_model_model import AiModelModel


class AiModelMapper:
    """
    Mapper for converting between AiModel domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: AiModelModel) -> AiModelEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy AiModel model

        Returns:
            AiModel domain entity
        """
        return AiModelEntity(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: AiModelEntity, existing_model: Optional[AiModelModel] = None) -> AiModelModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: AiModel domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy AiModel model
        """
        if existing_model:
            # Update existing model
            existing_model.name = entity.name
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model - don't set id, let database auto-generate it
            return AiModelModel(
                name=entity.name,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )

    @staticmethod
    def to_model_dict(entity: AiModelEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: AiModel domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "name": entity.name,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }

