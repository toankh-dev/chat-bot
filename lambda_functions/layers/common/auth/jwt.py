"""JWT authentication utilities"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import wraps

from ..utils.exceptions import UnauthorizedError


class JWTAuth:
    """JWT token management"""

    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.access_token_expire = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
        self.refresh_token_expire = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))

    def create_access_token(
        self,
        user_id: int,
        email: str,
        roles: List[str],
        permissions: List[str],
        additional_claims: Optional[Dict] = None
    ) -> str:
        """Create access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)

        payload = {
            'sub': str(user_id),
            'email': email,
            'roles': roles,
            'permissions': permissions,
            'type': 'access',
            'exp': expire,
            'iat': datetime.utcnow(),
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """Create refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire)

        payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'exp': expire,
            'iat': datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token has expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Invalid token")

    def extract_token_from_event(self, event: Dict) -> Optional[str]:
        """Extract token from Lambda event"""
        # Check Authorization header
        headers = event.get('headers', {})

        # Headers might be case-insensitive
        auth_header = headers.get('Authorization') or headers.get('authorization')

        if auth_header:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                return parts[1]

        # Check query string parameters (fallback)
        query_params = event.get('queryStringParameters', {})
        if query_params:
            return query_params.get('token')

        return None

    def get_current_user(self, event: Dict) -> Dict[str, Any]:
        """Get current user from event"""
        token = self.extract_token_from_event(event)

        if not token:
            raise UnauthorizedError("No authentication token provided")

        payload = self.verify_token(token)

        if payload.get('type') != 'access':
            raise UnauthorizedError("Invalid token type")

        return {
            'user_id': int(payload['sub']),
            'email': payload['email'],
            'roles': payload.get('roles', []),
            'permissions': payload.get('permissions', [])
        }


# Global instance
jwt_auth = JWTAuth()


def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    def wrapper(event, context):
        try:
            # Attach user info to event
            event['current_user'] = jwt_auth.get_current_user(event)
            return func(event, context)
        except UnauthorizedError as e:
            from ..utils.response import APIResponse
            return APIResponse.unauthorized(str(e))
        except Exception as e:
            from ..utils.response import APIResponse
            return APIResponse.internal_error(f"Authentication error: {str(e)}")

    return wrapper


def require_role(*required_roles: str):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            try:
                current_user = event.get('current_user')

                if not current_user:
                    current_user = jwt_auth.get_current_user(event)
                    event['current_user'] = current_user

                user_roles = current_user.get('roles', [])

                # Admin has access to everything
                if 'admin' in user_roles:
                    return func(event, context)

                # Check if user has any of the required roles
                if not any(role in user_roles for role in required_roles):
                    from ..utils.response import APIResponse
                    return APIResponse.forbidden(
                        f"Required roles: {', '.join(required_roles)}"
                    )

                return func(event, context)
            except UnauthorizedError as e:
                from ..utils.response import APIResponse
                return APIResponse.unauthorized(str(e))
            except Exception as e:
                from ..utils.response import APIResponse
                return APIResponse.internal_error(f"Authorization error: {str(e)}")

        return wrapper
    return decorator


def require_permission(*required_permissions: str):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            try:
                current_user = event.get('current_user')

                if not current_user:
                    current_user = jwt_auth.get_current_user(event)
                    event['current_user'] = current_user

                user_permissions = current_user.get('permissions', [])
                user_roles = current_user.get('roles', [])

                # Admin has all permissions
                if 'admin' in user_roles:
                    return func(event, context)

                # Check if user has all required permissions
                missing_permissions = [
                    perm for perm in required_permissions
                    if perm not in user_permissions
                ]

                if missing_permissions:
                    from ..utils.response import APIResponse
                    return APIResponse.forbidden(
                        f"Missing permissions: {', '.join(missing_permissions)}"
                    )

                return func(event, context)
            except UnauthorizedError as e:
                from ..utils.response import APIResponse
                return APIResponse.unauthorized(str(e))
            except Exception as e:
                from ..utils.response import APIResponse
                return APIResponse.internal_error(f"Authorization error: {str(e)}")

        return wrapper
    return decorator
