"""
Group entity to ORM model mapper.

Handles conversion between domain Group entity and SQLAlchemy Group model.
"""

from typing import Optional
from domain.entities.group import GroupEntity
from infrastructure.postgresql.models.group_model import Group as GroupModel


class GroupMapper:
    """
    Mapper for converting between Group domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: GroupModel) -> GroupEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy Group model

        Returns:
            Group domain entity
        """
        return GroupEntity(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: GroupEntity, existing_model: Optional[GroupModel] = None) -> GroupModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Group domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy Group model
        """
        if existing_model:
            # Update existing model
            existing_model.name = entity.name
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model
            return GroupModel(
                id=entity.id,
                name=entity.name,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )

    @staticmethod
    def to_model_dict(entity: GroupEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: Group domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "name": entity.name,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }