"""JWT authentication middleware."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.auth.jwt_handler import JWTHandler
from infrastructure.postgresql.connection.database import get_db_session
from domain.entities.user import UserEntity
from shared.interfaces.repositories.user_repository import UserRepository
from core.dependencies import get_user_repository
from core.errors import (
    AuthenticationError,
    InvalidTokenError,
    AuthorizationError
)

security = HTTPBearer()


def get_jwt_handler() -> JWTHandler:
    """Get JWT handler instance."""
    return JWTHandler()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> UserEntity:
    """
    Get current authenticated user from JWT token using Clean Architecture.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session
        jwt_handler: JWT handler instance

    Returns:
        UserEntity: Authenticated user

    Raises:
        AuthenticationError: If authentication fails
        InvalidTokenError: If token is invalid
        AuthorizationError: If user account is not active
    """
    # Import here to avoid circular dependency
    
    token = credentials.credentials

    try:
        payload = jwt_handler.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Token does not contain user ID")

        # Use dependency injection for repository
        user_repository: UserRepository = get_user_repository(session)
        user = await user_repository.find_by_id(int(user_id))

        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthorizationError("User account is not active")

        return user

    except (AuthenticationError, InvalidTokenError, AuthorizationError):
        raise
    except Exception as e:
        print("Authentication error:", str(e))
        raise AuthenticationError("Could not validate credentials")


async def require_admin(
    current_user: UserEntity = Depends(get_current_user)
) -> UserEntity:
    """
    Require user to be admin.

    Args:
        current_user: Authenticated user

    Returns:
        UserEntity: Admin user

    Raises:
        AuthorizationError: If user is not admin
    """
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required")
    return current_user
