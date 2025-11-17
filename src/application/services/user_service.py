from typing import List, Optional
from datetime import datetime
import bcrypt
from sqlalchemy import select
from domain.value_objects.email import Email
from core.errors import NotFoundError, ValidationError, ResourceConflictError
from domain.entities.user import UserEntity
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository
from infrastructure.postgresql.models.user_group_model import UserGroup as UserGroupModel


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_group_repository: Optional[UserGroupRepository] = None,
        group_repository: Optional[GroupRepository] = None,
        group_chatbot_repository: Optional[GroupChatbotRepository] = None,
        user_chatbot_repository: Optional[UserChatbotRepository] = None
    ):
        self.user_repository = user_repository
        self.user_group_repository = user_group_repository
        self.group_repository = group_repository
        self.group_chatbot_repository = group_chatbot_repository
        self.user_chatbot_repository = user_chatbot_repository

    async def get_user_by_id(self, user_id: int, include_groups: bool = True) -> UserEntity:
        user = await self.user_repository.find_by_id(str(user_id))
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        if include_groups and self.user_group_repository:
            groups = await self.user_group_repository.get_user_groups(user_id)
            user.groups = groups

        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        return await self.user_repository.find_all(skip=skip, limit=limit)

    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        is_admin: bool = False,
        group_ids: Optional[List[int]] = None,
        added_by: Optional[int] = None
    ) -> UserEntity:
        if not email or not email.strip():
            raise ValidationError("Email is required")

        if not name or not name.strip():
            raise ValidationError("Name is required")

        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        if group_ids:
            if not added_by:
                raise ValidationError("added_by is required when assigning groups")

            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = UserEntity(
            id=0,
            email=Email(email),
            username=email.split('@')[0],
            name=name.strip(),
            password_hash=password_hash,
            status="active",
            is_admin=is_admin
        )

        created_user = await self.user_repository.create(user)

        if group_ids and self.user_group_repository and created_user.id > 0:
            await self.user_group_repository.assign_user_to_groups(
                user_id=created_user.id,
                group_ids=group_ids,
                added_by=added_by
            )

        return created_user

    async def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        group_ids: Optional[List[int]] = None,
        updated_by: Optional[int] = None
    ) -> UserEntity:
        user = await self.get_user_by_id(user_id, include_groups=False)

        if name is not None:
            if not name or not name.strip():
                raise ValidationError("Name cannot be empty")
            user.name = name.strip()
            user.updated_at = datetime.utcnow()

        if is_active is not None:
            if not is_active and user.is_admin:
                first_admin = await self.user_repository.find_first_admin()
                if not first_admin:
                    raise NotFoundError("No admin users found in the system")
                if user_id == first_admin.id:
                    raise ValidationError("Cannot deactivate the account creator")

                active_admin_count = await self.user_repository.count_active_admins(exclude_user_id=user_id)
                if active_admin_count == 0:
                    raise ValidationError("Cannot deactivate the last active admin account")

            if is_active:
                user.activate()
            else:
                user.deactivate()

        updated_user = await self.user_repository.update(user)

        if group_ids is not None:
            if not updated_by:
                raise ValidationError("updated_by is required when updating group assignments")

            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

            if self.user_group_repository:
                await self.user_group_repository.assign_user_to_groups(
                    user_id=user_id,
                    group_ids=group_ids,
                    added_by=updated_by
                )

        return updated_user

    async def delete_user(self, user_id: int, deleted_by: int) -> bool:
        if not await self.user_repository.exists(str(user_id)):
            raise NotFoundError(f"User with ID {user_id} not found")

        if user_id == deleted_by:
            raise ValidationError("You cannot delete your own account")

        user = await self.user_repository.find_by_id(str(user_id))
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        if user.is_admin:
            first_admin = await self._get_first_admin()
            if deleted_by != first_admin.id:
                raise ValidationError("Only the account creator can delete admin accounts")
            if user_id == first_admin.id:
                raise ValidationError("The account creator cannot be deleted")

        conflict_reasons = []

        if self.user_group_repository and hasattr(self.user_group_repository, 'session'):
            try:
                result = await self.user_group_repository.session.execute(
                    select(UserGroupModel).where(UserGroupModel.user_id == user_id).limit(1)
                )
                if result.scalar_one_or_none():
                    conflict_reasons.append("user is assigned to groups")
            except Exception:
                pass

        if conflict_reasons:
            reason_text = ", ".join(conflict_reasons)
            raise ResourceConflictError(
                f"Cannot delete user: {reason_text}. Please reassign these relationships to another user first."
            )

        return await self.user_repository.delete(str(user_id))

    async def _get_first_admin(self) -> UserEntity:
        first_admin = await self.user_repository.find_first_admin()
        if not first_admin:
            raise NotFoundError("No admin users found in the system")
        return first_admin

    async def update_own_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> UserEntity:
        user = await self.get_user_by_id(user_id, include_groups=False)
        updated = False

        if name is not None:
            if not name or not name.strip():
                raise ValidationError("Name cannot be empty")
            user.name = name.strip()
            updated = True

        if email is not None:
            if not email or not email.strip():
                raise ValidationError("Email cannot be empty")

            if str(user.email) != email:
                existing_user = await self.user_repository.find_by_email(email)
                if existing_user and existing_user.id != user_id:
                    raise ValidationError("Email already registered")

                user.email = Email(email)
                user.username = email.split('@')[0]
                updated = True

        if updated:
            user.updated_at = datetime.utcnow()

        return await self.user_repository.update(user)

    async def change_own_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        user = await self.get_user_by_id(user_id, include_groups=False)

        if not current_password or not current_password.strip():
            raise ValidationError("Current password is required")

        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise ValidationError("Current password is incorrect")

        if current_password == new_password:
            raise ValidationError("New password must be different from current password")

        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user.password_hash = hashed_password
        user.updated_at = datetime.utcnow()
        await self.user_repository.update(user)

    async def change_password(self, user_id: int, new_password: str) -> UserEntity:
        user = await self.get_user_by_id(user_id, include_groups=False)

        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user.password_hash = hashed_password
        user.updated_at = datetime.utcnow()
        return await self.user_repository.update(user)
