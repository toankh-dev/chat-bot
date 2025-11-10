"""
UserGroup entity to ORM model mapper.

Handles conversion between domain UserGroup entity and SQLAlchemy UserGroup model.
"""

from typing import Optional
from domain.entities.user_group import UserGroupEntity
from infrastructure.postgresql.models.user_group_model import UserGroup as UserGroupModel


class UserGroupMapper:
    """
    Mapper for converting between UserGroup domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: UserGroupModel) -> UserGroupEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy UserGroup model

        Returns:
            UserGroup domain entity
        """
        return UserGroupEntity(
            id=None,  # No id column in table (composite primary key)
            user_id=model.user_id,
            group_id=model.group_id,
            added_by=model.added_by,
            created_at=model.joined_at
        )

    @staticmethod
    def to_model(entity: UserGroupEntity, existing_model: Optional[UserGroupModel] = None) -> UserGroupModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: UserGroup domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy UserGroup model
        """
        if existing_model:
            # Update existing model (rarely needed for junction tables)
            existing_model.user_id = entity.user_id
            existing_model.group_id = entity.group_id
            existing_model.added_by = entity.added_by
            existing_model.joined_at = entity.created_at.replace(tzinfo=None) if entity.created_at and entity.created_at.tzinfo else entity.created_at
            return existing_model
        else:
            # Create new model - remove timezone from datetime
            joined_at = entity.created_at.replace(tzinfo=None) if entity.created_at and entity.created_at.tzinfo else entity.created_at
            return UserGroupModel(
                user_id=entity.user_id,
                group_id=entity.group_id,
                added_by=entity.added_by,
                joined_at=joined_at
            )

    @staticmethod
    def to_model_dict(entity: UserGroupEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: UserGroup domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "user_id": entity.user_id,
            "group_id": entity.group_id,
            "added_by": entity.added_by,
            "joined_at": entity.created_at
        }