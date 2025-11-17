"""JWT handler interface for application layer.
"""
from typing import Protocol
from src.domain.entities.user import UserEntity

class IJWTHandler(Protocol):
    """
    Service for authentication operations.
    """

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        ...

    def hash_password(self, password: str) -> str:
        """Hash password."""
        ...
    
    async def authenticate_user(self, email: str, password: str) -> UserEntity:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain password

        Returns:
            UserModel: Authenticated user
        """
        ...
    
    async def register_user(self, email: str, password: str, name: str) -> UserEntity:
        """
        Register new user.

        Args:
            email: User email
            password: Plain password
            name: User full name

        Returns:
            UserEntity: Created user
        """
        ...
    
    def create_tokens(self, user: UserEntity) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: UserEntity to create tokens for

        Returns:
            dict: Contains access_token, refresh_token, and token_type
        """
        ...

