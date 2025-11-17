from fastapi import Depends
from typing import List
from schemas.user_schema import UserResponse, UserCreate, UserUpdate, UserProfileUpdate, ChangePasswordRequest
from domain.entities.user import UserEntity
from api.middlewares.jwt_middleware import get_current_user, require_admin
from usecases.user_use_cases import (
    GetCurrentUserUseCase,
    ListUsersUseCase,
    GetUserUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    UpdateOwnProfileUseCase,
    ChangePasswordUseCase
)
from core.dependencies import (
    get_current_user_use_case,
    get_list_users_use_case,
    get_user_use_case,
    get_create_user_use_case,
    get_update_user_use_case,
    get_delete_user_use_case,
    get_update_own_profile_use_case,
    get_change_password_use_case
)


async def get_current_user_profile(
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetCurrentUserUseCase = Depends(get_current_user_use_case)
) -> UserResponse:
    return await use_case.execute(current_user.id)


async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserEntity = Depends(require_admin),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case)
) -> List[UserResponse]:
    return await use_case.execute(skip=skip, limit=limit)


async def get_user(
    user_id: int,
    current_user: UserEntity = Depends(require_admin),
    use_case: GetUserUseCase = Depends(get_user_use_case)
) -> UserResponse:
    return await use_case.execute(user_id)


async def create_user(
    user_data: UserCreate,
    current_user: UserEntity = Depends(require_admin),
    use_case: CreateUserUseCase = Depends(get_create_user_use_case)
) -> UserResponse:
    return await use_case.execute(user_data, admin_id=current_user.id)


async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserEntity = Depends(require_admin),
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
) -> UserResponse:
    return await use_case.execute(user_id, user_data, admin_id=current_user.id)


async def delete_user(
    user_id: int,
    current_user: UserEntity = Depends(require_admin),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case)
) -> None:
    await use_case.execute(user_id, admin_id=current_user.id)


async def update_own_profile(
    profile_data: UserProfileUpdate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: UpdateOwnProfileUseCase = Depends(get_update_own_profile_use_case)
) -> UserResponse:
    return await use_case.execute(current_user.id, profile_data)


async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case)
) -> dict:
    await use_case.execute(current_user.id, password_data)
    return {"message": "Password changed successfully"}
