"""
User use cases.

Defines application-level use cases for user operations.
"""

from typing import List
from application.services.user_service import UserService
from infrastructure.postgresql.models import User
from schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse
)


class GetCurrentUserUseCase:
    """
    Use case for getting current user profile.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int) -> UserResponse:
        """
        Execute get current user use case.

        Args:
            user_id: Current user ID

        Returns:
            UserResponse: User profile data
        """
        user = await self.user_service.get_user_by_id(user_id)
        return UserResponse.model_validate(user)


class ListUsersUseCase:
    """
    Use case for listing users.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        Execute list users use case.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[UserResponse]: List of users
        """
        users = await self.user_service.list_users(skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]


class GetUserUseCase:
    """
    Use case for getting user by ID.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int) -> UserResponse:
        """
        Execute get user use case.

        Args:
            user_id: User ID

        Returns:
            UserResponse: User data
        """
        user = await self.user_service.get_user_by_id(user_id)
        return UserResponse.model_validate(user)


class CreateUserUseCase:
    """
    Use case for creating user.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, request: UserCreate) -> UserResponse:
        """
        Execute create user use case.

        Args:
            request: User creation data

        Returns:
            UserResponse: Created user data
        """
        user = await self.user_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            is_admin=request.is_admin
        )
        return UserResponse.model_validate(user)


class UpdateUserUseCase:
    """
    Use case for updating user.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: UserUpdate) -> UserResponse:
        """
        Execute update user use case.

        Args:
            user_id: User ID
            request: User update data

        Returns:
            UserResponse: Updated user data
        """
        user = await self.user_service.update_user(
            user_id=user_id,
            name=request.name,
            status=request.status
        )
        return UserResponse.model_validate(user)


class DeleteUserUseCase:
    """
    Use case for deleting user.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int) -> bool:
        """
        Execute delete user use case.

        Args:
            user_id: User ID

        Returns:
            bool: True if deleted
        """
        return await self.user_service.delete_user(user_id)
