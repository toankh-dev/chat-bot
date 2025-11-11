"""
User entity to ORM model mapper.

Handles conversion between domain User entity and SQLAlchemy User model.
"""

from typing import Optional
from domain.entities.user import UserEntity
from domain.value_objects.email import Email
from infrastructure.postgresql.models import UserModel


class UserMapper:
    """
    Mapper for converting between User domain entity and ORM model.

    This mapper isolates the domain layer from ORM-specific concerns.
    """

    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy User model

        Returns:
            User domain entity
        """
        return UserEntity(
            id=model.id,
            email=Email(model.email),
            username=model.email.split('@')[0],  # Derive username from email for now
            name=model.name,
            password_hash=model.password_hash,
            status=model.status,
            is_admin=model.is_admin,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=None  # Not tracked in current ORM model
        )

    @staticmethod
    def to_model(entity: UserEntity, existing_model: Optional[UserModel] = None) -> UserModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: User domain entity
            existing_model: Existing model to update (optional)

        Returns:
            SQLAlchemy User model
        """
        if existing_model:
            # Update existing model
            existing_model.email = str(entity.email)
            existing_model.name = entity.name
            existing_model.password_hash = entity.password_hash
            existing_model.status = entity.status
            existing_model.is_admin = entity.is_admin
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model - skip id if None to allow auto-generation
            model_data = {
                "email": str(entity.email),
                "name": entity.name,
                "password_hash": entity.password_hash,
                "status": entity.status,
                "is_admin": entity.is_admin,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at
            }
            # Only set id if entity has a valid id
            if entity.id is not None:
                model_data["id"] = entity.id
            
            return UserModel(**model_data)

    @staticmethod
    def to_model_dict(entity: UserEntity) -> dict:
        """
        Convert domain entity to dictionary for ORM model creation.

        Args:
            entity: User domain entity

        Returns:
            Dictionary with ORM model fields
        """
        return {
            "email": str(entity.email),
            "name": entity.name,
            "password_hash": entity.password_hash,
            "status": entity.status,
            "is_admin": entity.is_admin,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
