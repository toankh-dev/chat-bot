"""JWT authentication middleware."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.auth.jwt_handler import JWTHandler
from src.infrastructure.postgresql.pg_client import get_db_session
from src.infrastructure.postgresql.models import User
from src.infrastructure.postgresql.user_repository_impl import UserRepositoryImpl
from src.core.dependencies import get_jwt_handler

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session
        jwt_handler: JWT handler instance

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        payload = jwt_handler.decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user_repository = UserRepositoryImpl(db)
        user = await user_repository.find_by_id(int(user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require user to be admin.

    Args:
        current_user: Authenticated user

    Returns:
        User: Admin user

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
