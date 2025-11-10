"""Authentication controller."""

from fastapi import Depends, status
from schemas.auth_schema import LoginRequest, LoginResponse, RegisterRequest
from usecases.auth_use_cases import LoginUseCase, RegisterUseCase
from core.dependencies import get_login_use_case, get_register_use_case
from api.middlewares.jwt_middleware import get_current_user
from domain.entities.user import UserEntity


async def login(
    request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case)
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.

    Args:
        request: Login credentials
        use_case: Login use case instance

    Returns:
        LoginResponse: Access and refresh tokens
    """
    return await use_case.execute(request)


async def register(
    request: RegisterRequest,
    use_case: RegisterUseCase = Depends(get_register_use_case)
) -> LoginResponse:
    """
    Register a new user.

    Args:
        request: Registration data
        use_case: Register use case instance

    Returns:
        LoginResponse: Access and refresh tokens for new user
    """
    return await use_case.execute(request)


async def logout(
    current_user: UserEntity = Depends(get_current_user)
) -> dict:
    """
    Logout current user.

    In a stateless JWT system, logout is handled client-side by removing the token.
    This endpoint confirms the logout action and can be extended with token blacklisting
    if needed in the future.

    Args:
        current_user: Authenticated user

    Returns:
        dict: Logout confirmation message
    """
    return {
        "message": "Successfully logged out",
        "user_id": current_user.id
    }
