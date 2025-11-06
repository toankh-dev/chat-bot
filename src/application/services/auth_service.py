"""
Authentication service.

Handles user authentication and token management.
"""

from typing import Optional
from passlib.context import CryptContext
from src.shared.repositories.user_repository import UserRepository
from src.infrastructure.auth.jwt_handler import JWTHandler
from src.infrastructure.postgresql.models import User
from src.core.errors import AuthenticationError, ValidationError


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: JWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain password

        Returns:
            User: Authenticated user

        Raises:
            AuthenticationError: If authentication fails
        """
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not self.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if user.status != "active":
            raise AuthenticationError(f"User account is {user.status}")

        return user

    async def register_user(self, email: str, password: str, name: str) -> User:
        """
        Register new user.

        Args:
            email: User email
            password: Plain password
            name: User full name

        Returns:
            User: Created user

        Raises:
            ValidationError: If email already exists
        """
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_password = self.hash_password(password)

        user = User(
            email=email,
            password_hash=hashed_password,
            name=name,
            is_admin=False,
            status="active"
        )

        return await self.user_repository.create(user)

    def create_tokens(self, user: User) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: User to create tokens for

        Returns:
            dict: Contains access_token, refresh_token, and token_type
        """
        access_token = self.jwt_handler.create_access_token(
            subject=str(user.id),
            additional_claims={"email": user.email, "is_admin": user.is_admin}
        )

        refresh_token = self.jwt_handler.create_refresh_token(
            subject=str(user.id)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
