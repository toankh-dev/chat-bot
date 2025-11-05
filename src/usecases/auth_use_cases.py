"""
Authentication use cases.

Defines application-level use cases for authentication operations.
"""

from src.application.services.auth_service import AuthService
from src.schemas.auth_schema import LoginRequest, RegisterRequest, LoginResponse


class LoginUseCase:
    """
    Use case for user login.
    """

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def execute(self, request: LoginRequest) -> LoginResponse:
        """
        Execute login use case.

        Args:
            request: Login request data

        Returns:
            LoginResponse: Access and refresh tokens
        """
        user = await self.auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )

        tokens = self.auth_service.create_tokens(user)

        return LoginResponse(**tokens)


class RegisterUseCase:
    """
    Use case for user registration.
    """

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def execute(self, request: RegisterRequest) -> LoginResponse:
        """
        Execute registration use case.

        Args:
            request: Registration request data

        Returns:
            LoginResponse: Access and refresh tokens for new user
        """
        user = await self.auth_service.register_user(
            email=request.email,
            password=request.password,
            name=request.name
        )

        tokens = self.auth_service.create_tokens(user)

        return LoginResponse(**tokens)
