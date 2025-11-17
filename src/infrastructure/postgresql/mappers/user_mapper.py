from typing import Optional
from domain.entities.user import UserEntity
from domain.value_objects.email import Email
from infrastructure.postgresql.models import UserModel


class UserMapper:
    @staticmethod
    def _to_naive_datetime(dt):
        if dt is None:
            return None
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        return UserEntity(
            id=model.id,
            email=Email(model.email),
            username=model.email.split('@')[0],
            name=model.name,
            password_hash=model.password_hash,
            status=model.status,
            is_admin=model.is_admin,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=None
        )

    @staticmethod
    def to_model(entity: UserEntity, existing_model: Optional[UserModel] = None) -> UserModel:
        if existing_model:
            existing_model.email = str(entity.email)
            existing_model.name = entity.name
            existing_model.password_hash = entity.password_hash
            existing_model.status = entity.status
            existing_model.is_admin = entity.is_admin
            existing_model.updated_at = UserMapper._to_naive_datetime(entity.updated_at)
            return existing_model
        else:
            model_data = {
                "email": str(entity.email),
                "name": entity.name,
                "password_hash": entity.password_hash,
                "status": entity.status,
                "is_admin": entity.is_admin,
                "created_at": UserMapper._to_naive_datetime(entity.created_at),
                "updated_at": UserMapper._to_naive_datetime(entity.updated_at)
            }
            if entity.id is not None and entity.id > 0:
                model_data["id"] = entity.id
            return UserModel(**model_data)

    @staticmethod
    def to_model_dict(entity: UserEntity) -> dict:
        return {
            "email": str(entity.email),
            "name": entity.name,
            "password_hash": entity.password_hash,
            "status": entity.status,
            "is_admin": entity.is_admin,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        }
