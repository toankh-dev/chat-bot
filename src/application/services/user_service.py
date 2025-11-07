"""
User service.

Handles user management business logic.
"""

from typing import List, Optional
from passlib.context import CryptContext
from shared.interfaces.repositories.user_repository import UserRepository
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.uuid_vo import UUID
from core.errors import NotFoundError, ValidationError


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """
    Service for user management operations.

    Works exclusively with domain entities, not ORM models.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User: Found user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
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
        is_admin: bool = False
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            password: Plain password
            name: User full name
            is_admin: Whether user is admin

        Returns:
            User: Created user

        Raises:
            ValidationError: If email already exists
        """
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_password = pwd_context.hash(password)

        # Create domain entity
        user = User(
            id=UUID.generate(),
            email=Email(email),
            username=email.split('@')[0],  # Derive username from email
            full_name=name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=is_admin
        )

        return await self.user_repository.create(user)

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            name: New name (optional)
            is_active: Active status (optional)

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user_by_id(user_id)

        # Update domain entity using its methods
        if name is not None:
            # Update the full_name attribute directly (domain entity doesn't have .name)
            user = User(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=name,
                hashed_password=user.hashed_password,
                is_active=user.is_active if is_active is None else is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        elif is_active is not None:
            if is_active:
                user.activate()
            else:
                user.deactivate()

        return await self.user_repository.update(user)

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
        new_hash = pwd_context.hash(new_password)
        user.update_password(new_hash)
        return await self.user_repository.update(user)
