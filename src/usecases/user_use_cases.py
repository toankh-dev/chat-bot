from typing import List
from src.domain.entities.user import UserEntity
from application.services.user_service import UserService
from schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserProfileUpdate,
    ChangePasswordRequest,
    UserResponse
)


def _convert_entity_to_response(user: UserEntity) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=str(user.email),
        name=user.name,
        is_admin=user.is_admin,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        groups=getattr(user, 'groups', None)
    )


class GetCurrentUserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int) -> UserResponse:
        user = await self.user_service.get_user_by_id(user_id)
        return _convert_entity_to_response(user)


class ListUsersUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_service.list_users(skip=skip, limit=limit)
        responses = []
        for user in users:
            if self.user_service.user_group_repository:
                groups = await self.user_service.user_group_repository.get_user_groups(user.id)
                user.groups = groups
            responses.append(_convert_entity_to_response(user))
        return responses


class GetUserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int) -> UserResponse:
        user = await self.user_service.get_user_by_id(user_id)
        return _convert_entity_to_response(user)


class CreateUserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, request: UserCreate, admin_id: int) -> UserResponse:
        user = await self.user_service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            is_admin=request.is_admin,
            group_ids=request.group_ids,
            added_by=admin_id
        )
        user = await self.user_service.get_user_by_id(user.id, include_groups=True)
        return _convert_entity_to_response(user)


class UpdateUserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: UserUpdate, admin_id: int) -> UserResponse:
        user = await self.user_service.update_user(
            user_id=user_id,
            name=request.name,
            is_active=request.is_active,
            group_ids=request.group_ids,
            updated_by=admin_id
        )
        user = await self.user_service.get_user_by_id(user_id, include_groups=True)
        return _convert_entity_to_response(user)


class DeleteUserUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, admin_id: int) -> bool:
        return await self.user_service.delete_user(user_id, deleted_by=admin_id)


class UpdateOwnProfileUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: UserProfileUpdate) -> UserResponse:
        user = await self.user_service.update_own_profile(
            user_id=user_id,
            name=request.name,
            email=request.email
        )
        user = await self.user_service.get_user_by_id(user_id, include_groups=True)
        return _convert_entity_to_response(user)


class ChangePasswordUseCase:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    async def execute(self, user_id: int, request: ChangePasswordRequest) -> None:
        await self.user_service.change_own_password(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
