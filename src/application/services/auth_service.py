import bcrypt
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.services.auth.jwt_handler import IJWTHandler
from domain.entities.user import UserEntity
from domain.value_objects.email import Email
from core.errors import AuthenticationError, ValidationError, InvalidTokenError


class AuthService:
    def __init__(self, user_repository: UserRepository, jwt_handler: IJWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    async def authenticate_user(self, email: str, password: str) -> UserEntity:
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not self.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is not active")

        return user

    async def register_user(self, email: str, password: str, name: str) -> UserEntity:
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        password_hash = self.hash_password(password)

        user = UserEntity(
            id=0,
            email=Email(email),
            username=email.split('@')[0],
            name=name,
            password_hash=password_hash,
            status="active",
            is_admin=False
        )

        return await self.user_repository.create(user)

    def create_tokens(self, user: UserEntity) -> dict:
        access_token = self.jwt_handler.create_access_token(
            subject=str(user.id),
            additional_claims={"email": str(user.email), "is_admin": user.is_admin}
        )

        refresh_token = self.jwt_handler.create_refresh_token(
            subject=str(user.id)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        payload = self.jwt_handler.decode_token(refresh_token)
        
        token_type = payload.get("type")
        if token_type != "refresh":
            raise InvalidTokenError(
                message=f"Invalid token type. Expected refresh, got {token_type}"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token: missing user ID")
        
        user = await self.user_repository.find_by_id(str(user_id))
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is not active")
        
        return self.create_tokens(user)
