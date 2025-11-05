"""
User service.

Handles user management business logic.
"""

from typing import List, Optional
from passlib.context import CryptContext
from src.infrastructure.postgresql.user_repository_impl import UserRepositoryImpl
from src.infrastructure.postgresql.models import User
from src.core.errors import NotFoundError, ValidationError


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """
    Service for user management operations.
    """

    def __init__(self, user_repository: UserRepositoryImpl):
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int) -> User:
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

        user = User(
            email=email,
            password_hash=hashed_password,
            name=name,
            is_admin=is_admin,
            status="active"
        )

        return await self.user_repository.create(user)

    async def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        status: Optional[str] = None
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            name: New name (optional)
            status: New status (optional)

        Returns:
            User: Updated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user_by_id(user_id)

        if name is not None:
            user.name = name
        if status is not None:
            if status not in ["active", "disabled", "suspended"]:
                raise ValidationError(f"Invalid status: {status}")
            user.status = status

        return await self.user_repository.update(user)

    async def delete_user(self, user_id: int) -> bool:
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

    async def change_password(self, user_id: int, new_password: str) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            new_password: New plain password

        Returns:
            User: Updated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user_by_id(user_id)
        user.password_hash = pwd_context.hash(new_password)
        return await self.user_repository.update(user)
