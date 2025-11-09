"""
User entity to ORM model mapper.

Handles conversion between domain User entity and SQLAlchemy User model.
"""

from typing import Optional
from domain.entities.user import UserEntity
from domain.value_objects.email import Email
from domain.value_objects.uuid_vo import UUID as UUIDValue
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
            id=UUIDValue.from_string(str(model.id)),
            email=Email(model.email),
            username=model.email.split('@')[0],  # Derive username from email for now
            full_name=model.name,
            hashed_password=model.password_hash,
            is_active=model.status == "active",
            is_superuser=model.is_admin,
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
            existing_model.name = entity.full_name
            existing_model.password_hash = entity.hashed_password
            existing_model.status = "active" if entity.is_active else "disabled"
            existing_model.is_admin = entity.is_superuser
            existing_model.updated_at = entity.updated_at
            return existing_model
        else:
            # Create new model
            return UserModel(
                id=int(str(entity.id).replace('-', '')[:8], 16) % 2147483647,  # Convert UUID to int for demo
                email=str(entity.email),
                name=entity.full_name,
                password_hash=entity.hashed_password,
                status="active" if entity.is_active else "disabled",
                is_admin=entity.is_superuser,
                created_at=entity.created_at,
                updated_at=entity.updated_at
            )

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
            "name": entity.full_name,
            "password_hash": entity.hashed_password,
            "status": "active" if entity.is_active else "disabled",
            "is_admin": entity.is_superuser,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
