"""User management controller."""

from fastapi import Depends, status
from typing import List
from src.schemas.user_schema import UserResponse, UserCreate, UserUpdate
from src.infrastructure.postgresql.models import User
from src.api.middlewares.jwt_middleware import get_current_user, require_admin
from src.usecases.user_use_cases import (
    GetCurrentUserUseCase,
    ListUsersUseCase,
    GetUserUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)
from src.core.dependencies import (
    get_current_user_use_case,
    get_list_users_use_case,
    get_user_use_case,
    get_create_user_use_case,
    get_update_user_use_case,
    get_delete_user_use_case
)


async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    use_case: GetCurrentUserUseCase = Depends(get_current_user_use_case)
) -> UserResponse:
    """
    Get current user profile.

    Args:
        current_user: Authenticated user
        use_case: Get current user use case instance

    Returns:
        UserResponse: Current user data
    """
    return await use_case.execute(current_user.id)


async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case)
) -> List[UserResponse]:
    """
    List all users (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated admin user
        use_case: List users use case instance

    Returns:
        List[UserResponse]: List of users
    """
    return await use_case.execute(skip=skip, limit=limit)


async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    use_case: GetUserUseCase = Depends(get_user_use_case)
) -> UserResponse:
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Authenticated admin user
        use_case: Get user use case instance

    Returns:
        UserResponse: User data
    """
    return await use_case.execute(user_id)


async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    use_case: CreateUserUseCase = Depends(get_create_user_use_case)
) -> UserResponse:
    """
    Create new user (admin only).

    Args:
        user_data: User creation data
        current_user: Authenticated admin user
        use_case: Create user use case instance

    Returns:
        UserResponse: Created user data with group assignments
    """
    return await use_case.execute(user_data, admin_id=current_user.id)


async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
) -> UserResponse:
    """
    Update user (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        current_user: Authenticated admin user
        use_case: Update user use case instance

    Returns:
        UserResponse: Updated user data with group assignments
    """
    return await use_case.execute(user_id, user_data, admin_id=current_user.id)


async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case)
) -> None:
    """
    Delete user (admin only).

    Args:
        user_id: User ID
        current_user: Authenticated admin user
        use_case: Delete user use case instance
    """
    await use_case.execute(user_id)
