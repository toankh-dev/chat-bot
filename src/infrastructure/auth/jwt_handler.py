"""
JWT token handling for authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings
from core.logger import logger
from core.errors import TokenExpiredError, InvalidTokenError


class JWTHandler:
    """
    JWT token handler for authentication.

    Handles token generation, validation, and password hashing.
    """

    def __init__(self):
        """Initialize JWT handler."""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: Token subject (usually user ID)
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Access token created for subject: {subject}")

        return encoded_jwt

    def create_refresh_token(
        self,
        subject: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: Token subject (usually user ID)
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        if additional_claims:
            to_encode.update(additional_claims)

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Refresh token created for subject: {subject}")

        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise TokenExpiredError()

        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise InvalidTokenError(message=f"Invalid token: {str(e)}")

    def get_token_subject(self, token: str) -> str:
        """
        Extract subject from JWT token.

        Args:
            token: JWT token string

        Returns:
            Token subject (user ID)

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
        """
        payload = self.decode_token(token)
        subject = payload.get("sub")

        if not subject:
            raise InvalidTokenError(message="Token does not contain subject")

        return subject

    def verify_token_type(self, token: str, expected_type: str) -> bool:
        """
        Verify that token is of expected type.

        Args:
            token: JWT token string
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            True if token type matches

        Raises:
            InvalidTokenError: If token type doesn't match
        """
        payload = self.decode_token(token)
        token_type = payload.get("type")

        if token_type != expected_type:
            raise InvalidTokenError(
                message=f"Invalid token type. Expected {expected_type}, got {token_type}"
            )

        return True


# Singleton instance
_jwt_handler = None


def get_jwt_handler() -> JWTHandler:
    """Get singleton JWT handler instance."""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler
