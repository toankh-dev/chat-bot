"""
User service.

Handles user management business logic.
"""

from typing import List, Optional
import bcrypt
from datetime import datetime, timezone
from domain.value_objects.email import Email
from domain.value_objects.uuid_vo import UUID
from core.errors import NotFoundError, ValidationError
from domain.entities.user import User
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository
from shared.interfaces.repositories.user_repository import UserRepository


class UserService:
    """
    Service for user management operations.

    Works exclusively with domain entities, not ORM models.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_group_repository: Optional[UserGroupRepository] = None,
        group_repository: Optional[GroupRepository] = None
    ):
        self.user_repository = user_repository
        self.user_group_repository = user_group_repository
        self.group_repository = group_repository

    async def get_user_by_id(self, user_id: int, include_groups: bool = True) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID
            include_groups: Whether to load user's groups

        Returns:
            User: Found user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Load groups if requested
        if include_groups and self.user_group_repository:
            groups = await self.user_group_repository.get_user_groups(user_id)
            # Attach groups to user object for response
            user.groups = groups

        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        List all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[User]: List of users
        """
        return await self.user_repository.find_all(skip=skip, limit=limit)

    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        is_admin: bool = False,
        group_ids: Optional[List[int]] = None,
        added_by: Optional[int] = None
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            password: Plain password
            name: User full name
            is_admin: Whether user is admin
            group_ids: Optional list of group IDs to assign user to
            added_by: User ID of admin creating this user

        Returns:
            User: Created user

        Raises:
            ValidationError: If email already exists or invalid group IDs
        """
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        # Validate group IDs if provided
        if group_ids:
            # added_by is required when assigning groups
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

        # Create domain entity
        user = User(
            id=0,  # Will be set by database
            email=Email(email),
            username=email.split('@')[0],  # Derive username from email
            name=name,
            password_hash=password_hash,
            status="active",
            is_admin=is_admin
        )

        created_user = await self.user_repository.create(user)

        # Assign to groups if provided
        # Note: added_by has already been validated above if group_ids are provided
        if group_ids and self.user_group_repository:
            await self.user_group_repository.assign_user_to_groups(
                user_id=created_user.id,
                group_ids=group_ids,
                added_by=added_by  # type: ignore  # added_by is validated to be not None when group_ids is not empty
            )

        return created_user

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        group_ids: Optional[List[int]] = None,
        updated_by: Optional[int] = None
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            name: New name (optional)
            is_active: Active status (optional)
            status: New status (optional)
            group_ids: New list of group IDs (replaces existing, optional)
            updated_by: User ID of admin updating this user

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If invalid status or group IDs
        """
        user = await self.get_user_by_id(user_id)

        # Update domain entity using its methods
        if name is not None:
            # Update the full_name attribute directly (domain entity doesn't have .name)
            user = User(
                id=user.id,
                email=user.email,
                username=user.username,
                name=name,
                password_hash=user.password_hash,
                status=user.status if status is None else status,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        elif status is not None:
            user.status = status
            user.updated_at = datetime.now(timezone.utc)

        updated_user = await self.user_repository.update(user)

        # Update group assignments if provided
        if group_ids is not None:
            # updated_by is required when updating group assignments
            if not updated_by:
                raise ValidationError("updated_by is required when updating group assignments")

            # Validate group IDs
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

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user.

        Args:
            user_id: User ID

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If user not found
        """
        if not await self.user_repository.exists(user_id):
            raise NotFoundError(f"User with ID {user_id} not found")

        return await self.user_repository.delete(user_id)

    async def change_password(self, user_id: str, new_password: str) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            new_password: New plain password

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user_by_id(user_id)
        user.password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        return await self.user_repository.update(user)
