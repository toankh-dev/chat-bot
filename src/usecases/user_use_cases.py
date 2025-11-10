"""
User use cases.

Defines application-level use cases for user operations.
"""

from typing import List
from application.services.user_service import UserService
from infrastructure.postgresql.models import UserModel
from domain.entities.user import UserEntity
from schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserProfileUpdate,
    ChangePasswordRequest,
    UserResponse
)


def _convert_entity_to_response(user: UserEntity) -> UserResponse:
    """Convert UserEntity to UserResponse."""
    return UserResponse(
        id=user.id,
        email=str(user.email),
        name=user.full_name,
        is_admin=user.is_superuser,
        status="active" if user.is_active else "inactive",
        created_at=user.created_at,
        updated_at=user.updated_at,
        groups=getattr(user, 'groups', None)
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
        return _convert_entity_to_response(user)


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
        # Load groups for each user
        responses = []
        for user in users:
            # Load groups for this user using integer ID directly
            if self.user_service.user_group_repository:
                groups = await self.user_service.user_group_repository.get_user_groups(user.id)
                # Attach groups to user object
                user.groups = groups
            
            responses.append(_convert_entity_to_response(user))
        return responses


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
        return _convert_entity_to_response(user)


class CreateUserUseCase:
    """
    Use case for creating user.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, request: UserCreate, admin_id: int) -> UserResponse:
        """
        Execute create user use case.

        Args:
            request: User creation data
            admin_id: ID of admin creating the user

        Returns:
            UserResponse: Created user data
        """
        user = await self.user_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            is_admin=request.is_admin,
            group_ids=request.group_ids,
            added_by=admin_id
        )

        # Load groups for response
        user = await self.user_service.get_user_by_id(user.id, include_groups=True)
        return _convert_entity_to_response(user)


class UpdateUserUseCase:
    """
    Use case for updating user.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: UserUpdate, admin_id: int) -> UserResponse:
        """
        Execute update user use case.

        Args:
            user_id: User ID
            request: User update data
            admin_id: ID of admin updating the user

        Returns:
            UserResponse: Updated user data
        """
        user = await self.user_service.update_user(
            user_id=user_id,
            name=request.name,
            is_active=request.is_active,
            group_ids=request.group_ids,
            updated_by=admin_id
        )

        # Load groups for response
        user = await self.user_service.get_user_by_id(user_id, include_groups=True)
        return _convert_entity_to_response(user)


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


class UpdateOwnProfileUseCase:
    """
    Use case for updating own profile (logged-in user).
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: UserProfileUpdate) -> UserResponse:
        """
        Execute update own profile use case.

        Args:
            user_id: Current user ID (from JWT)
            request: Profile update data

        Returns:
            UserResponse: Updated user data
        """
        user = await self.user_service.update_own_profile(
            user_id=user_id,
            name=request.name,
            email=request.email
        )

        # Load groups for response
        user = await self.user_service.get_user_by_id(user_id, include_groups=True)
        return _convert_entity_to_response(user)


class ChangePasswordUseCase:
    """
    Use case for changing own password.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: ChangePasswordRequest) -> None:
        """
        Execute change password use case.

        Args:
            user_id: Current user ID (from JWT)
            request: Password change request with current and new password

        Raises:
            ValidationError: If current password is incorrect
        """
        await self.user_service.change_own_password(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
