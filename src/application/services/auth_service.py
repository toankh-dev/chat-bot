"""
Authentication service.

Handles user authentication and token management.
"""

from typing import Optional
import bcrypt
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.services.auth.jwt_handler import IJWTHandler
from domain.entities.user import UserEntity
from domain.value_objects.email import Email
from core.errors import AuthenticationError, ValidationError

class AuthService:
    """
    Service for authentication operations.
    """

    def __init__(self, user_repository: UserRepository, jwt_handler: IJWTHandler):
        self.user_repository = user_repository
        self.jwt_handler = jwt_handler

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def hash_password(self, password: str) -> str:
        """Hash password."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    async def authenticate_user(self, email: str, password: str) -> UserEntity:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain password

        Returns:
            UserModel: Authenticated user

        Raises:
            AuthenticationError: If authentication fails
        """
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not self.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is not active")

        return user

    async def register_user(self, email: str, password: str, name: str) -> UserEntity:
        """
        Register new user.

        Args:
            email: User email
            password: Plain password
            name: User full name

        Returns:
            UserModel: Created user

        Raises:
            ValidationError: If email already exists
        """
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_password = self.hash_password(password)

        # Build a domain User entity and persist via repository
        # ID will be set by database auto-increment
        user = UserEntity(
            id=0,  # Temporary ID, will be set by database
            email=Email(email),
            username=email.split('@')[0],
            full_name=name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False
        )

        return await self.user_repository.create(user)

    def create_tokens(self, user: UserEntity) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: User to create tokens for

        Returns:
            dict: Contains access_token, refresh_token, and token_type
        """
        access_token = self.jwt_handler.create_access_token(
            subject=str(user.id),
            additional_claims={"email": str(user.email), "is_admin": user.is_superuser}
        )

        refresh_token = self.jwt_handler.create_refresh_token(
            subject=str(user.id)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
