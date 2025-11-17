from application.services.auth_service import AuthService
from schemas.auth_schema import LoginRequest, RegisterRequest, LoginResponse, RefreshTokenRequest


class LoginUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def execute(self, request: LoginRequest) -> LoginResponse:
        user = await self.auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        tokens = self.auth_service.create_tokens(user)
        return LoginResponse(**tokens)


class RegisterUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def execute(self, request: RegisterRequest) -> LoginResponse:
        user = await self.auth_service.register_user(
            email=request.email,
            password=request.password,
            name=request.name
        )
        tokens = self.auth_service.create_tokens(user)
        return LoginResponse(**tokens)


class RefreshTokenUseCase:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def execute(self, request: RefreshTokenRequest) -> LoginResponse:
        tokens = await self.auth_service.refresh_tokens(request.refresh_token)
        return LoginResponse(**tokens)
