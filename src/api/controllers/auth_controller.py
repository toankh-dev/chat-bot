from fastapi import Depends
from schemas.auth_schema import LoginRequest, LoginResponse, RegisterRequest, LogoutResponse, RefreshTokenRequest
from usecases.auth_use_cases import LoginUseCase, RegisterUseCase, RefreshTokenUseCase
from core.dependencies import get_login_use_case, get_register_use_case, get_refresh_token_use_case
from api.middlewares.jwt_middleware import get_current_user
from domain.entities.user import UserEntity


async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
) -> LoginResponse:
    return await use_case.execute(request)


async def register(
    request: RegisterRequest,
    use_case: RegisterUseCase = Depends(get_register_use_case)
) -> LoginResponse:
    return await use_case.execute(request)


async def refresh_token(
    request: RefreshTokenRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case)
) -> LoginResponse:
    return await use_case.execute(request)


async def logout(
    current_user: UserEntity = Depends(get_current_user)
) -> LogoutResponse:
    return LogoutResponse(
        message="Successfully logged out",
        user_id=current_user.id
    )
