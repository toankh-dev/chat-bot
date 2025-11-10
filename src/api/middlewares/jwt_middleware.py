"""JWT authentication middleware."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.auth.jwt_handler import JWTHandler
from infrastructure.postgresql.connection.database import get_db_session
from domain.entities.user import UserEntity
from infrastructure.postgresql.repositories.user_repository import UserRepositoryImpl
from core.dependencies import get_jwt_handler

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> UserEntity:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session
        jwt_handler: JWT handler instance

    Returns:
        UserModel: Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        payload = jwt_handler.decode_token(token)
        user_id = payload.get("sub")
        print("payload:", payload)
        print("Authenticated user ID:", user_id)
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

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        print("Authentication error:", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def require_admin(
    current_user: UserEntity = Depends(get_current_user)
) -> UserEntity:
    """
    Require user to be admin.

    Args:
        current_user: Authenticated user

    Returns:
        UserModel: Admin user

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
