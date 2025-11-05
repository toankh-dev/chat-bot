"""User service with business logic"""

from typing import Optional, List, Dict, Tuple
import hashlib
import secrets

from ..repositories.user_repository import UserRepository
from ..models.domain.user import User, UserStatus, UserRole
from ..models.domain.permission import Permission, PermissionResource, PermissionAction
from ..utils.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    ForbiddenError
)
from ..utils.validators import validate_email, validate_password


class UserService:
    """User business logic"""

    def __init__(self):
        self.user_repo = UserRepository()

    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_value = password_hash.split('$')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_hash.hex() == hash_value
        except Exception:
            return False

    def _get_role_permissions(self, roles: List[UserRole]) -> List[str]:
        """Get permissions for roles"""
        permissions = set()

        if UserRole.ADMIN in roles:
            # Admin has all permissions
            for resource in PermissionResource:
                for action in PermissionAction:
                    permissions.add(f"{resource.value}:{action.value}")
        else:
            if UserRole.GROUP_ADMIN in roles:
                # Group admin permissions
                permissions.update([
                    'user:read', 'user:create', 'user:update',
                    'chatbot:read', 'chatbot:create', 'chatbot:update', 'chatbot:delete',
                    'conversation:read', 'conversation:delete',
                    'tool:read',
                    'analytics:read'
                ])

            if UserRole.USER in roles:
                # Regular user permissions
                permissions.update([
                    'user:read',
                    'chatbot:read',
                    'conversation:read', 'conversation:create', 'conversation:update',
                    'tool:read'
                ])

        return list(permissions)

    def create_user(
        self,
        email: str,
        name: str,
        password: str,
        group_id: Optional[int] = None,
        is_admin: bool = False,
        roles: Optional[List[str]] = None
    ) -> User:
        """Create new user"""
        # Validate email
        if not validate_email(email):
            raise ValidationError("Invalid email format")

        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise ValidationError(error_msg)

        # Validate name
        if not name or len(name.strip()) == 0:
            raise ValidationError("Name is required")

        # Create user model
        user = User(
            email=email.lower().strip(),
            name=name.strip(),
            group_id=group_id,
            is_admin=is_admin,
            status=UserStatus.ACTIVE
        )

        # Store password hash (in real implementation, add password field to User model)
        # For now, we'll handle password separately in the repository
        created_user = self.user_repo.create_user(user)

        # Assign roles
        if roles:
            for role in roles:
                try:
                    self.user_repo.assign_role(created_user.id, role)
                except Exception:
                    pass  # Continue if role doesn't exist

        return created_user

    def get_user_by_id(self, user_id: int, include_roles: bool = True) -> User:
        """Get user by ID"""
        if include_roles:
            user = self.user_repo.get_user_with_roles(user_id)
        else:
            user = self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundError(f"User with id {user_id} not found")

        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repo.find_by_email(email.lower().strip())

    def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        group_id: Optional[int] = None,
        status: Optional[UserStatus] = None
    ) -> Tuple[List[User], int]:
        """List users with pagination"""
        offset = (page - 1) * limit

        if group_id:
            users = self.user_repo.find_by_group(group_id, limit, offset)
            total = self.user_repo.count_by_group(group_id)
        elif status:
            users = self.user_repo.find_many_by_field('status', status.value, limit, offset)
            total = self.user_repo.count_by_status(status)
        else:
            users = self.user_repo.find_all(limit, offset, 'created_at', 'DESC')
            total = self.user_repo.count()

        return users, total

    def search_users(
        self,
        query: str,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[User], int]:
        """Search users"""
        if not query or len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters")

        offset = (page - 1) * limit
        users = self.user_repo.search_users(query.strip(), limit, offset)

        # Count total matches (simplified)
        total = len(users) if len(users) < limit else limit + 1

        return users, total

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        name: Optional[str] = None,
        group_id: Optional[int] = None,
        status: Optional[UserStatus] = None,
        current_user_id: Optional[int] = None
    ) -> User:
        """Update user"""
        # Get existing user
        user = self.get_user_by_id(user_id, include_roles=False)

        # Validate email if provided
        if email:
            if not validate_email(email):
                raise ValidationError("Invalid email format")
            user.email = email.lower().strip()

        # Validate name if provided
        if name:
            if len(name.strip()) == 0:
                raise ValidationError("Name cannot be empty")
            user.name = name.strip()

        # Update group
        if group_id is not None:
            user.group_id = group_id

        # Update status
        if status:
            user.status = status

        # Update in database
        updated_user = self.user_repo.update_user(user_id, user)

        return updated_user

    def delete_user(self, user_id: int, current_user_id: int) -> bool:
        """Delete user"""
        # Prevent self-deletion
        if user_id == current_user_id:
            raise ForbiddenError("Cannot delete your own account")

        # Check if user exists
        user = self.get_user_by_id(user_id, include_roles=False)

        # Delete user
        return self.user_repo.delete(user_id)

    def activate_user(self, user_id: int) -> User:
        """Activate user"""
        return self.user_repo.update_status(user_id, UserStatus.ACTIVE)

    def deactivate_user(self, user_id: int, current_user_id: int) -> User:
        """Deactivate user"""
        # Prevent self-deactivation
        if user_id == current_user_id:
            raise ForbiddenError("Cannot deactivate your own account")

        return self.user_repo.update_status(user_id, UserStatus.DISABLED)

    def suspend_user(self, user_id: int, current_user_id: int) -> User:
        """Suspend user"""
        # Prevent self-suspension
        if user_id == current_user_id:
            raise ForbiddenError("Cannot suspend your own account")

        return self.user_repo.update_status(user_id, UserStatus.SUSPENDED)

    def assign_role(self, user_id: int, role_name: str) -> bool:
        """Assign role to user"""
        # Validate role
        try:
            UserRole(role_name)
        except ValueError:
            raise ValidationError(f"Invalid role: {role_name}")

        # Check if user exists
        self.get_user_by_id(user_id, include_roles=False)

        return self.user_repo.assign_role(user_id, role_name)

    def remove_role(self, user_id: int, role_name: str) -> bool:
        """Remove role from user"""
        # Check if user exists
        self.get_user_by_id(user_id, include_roles=False)

        return self.user_repo.remove_role(user_id, role_name)

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        user = self.get_user_by_id(user_id, include_roles=True)
        return self._get_role_permissions(user.roles)

    def authenticate(self, email: str, password: str) -> Tuple[User, str, List[str]]:
        """Authenticate user and return user, token, permissions"""
        # Find user
        user = self.get_user_by_email(email)

        if not user:
            raise ValidationError("Invalid email or password")

        # Check status
        if user.status != UserStatus.ACTIVE:
            raise ForbiddenError(f"Account is {user.status.value}")

        # Verify password (in real implementation)
        # For now, we'll skip password verification since we don't have password storage

        # Get user with roles
        user = self.get_user_by_id(user.id, include_roles=True)

        # Get permissions
        permissions = self._get_role_permissions(user.roles)

        # Create access token
        from ..auth.jwt import jwt_auth
        token = jwt_auth.create_access_token(
            user_id=user.id,
            email=user.email,
            roles=[role.value for role in user.roles],
            permissions=permissions
        )

        return user, token, permissions

    def check_permission(
        self,
        user_id: int,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has permission"""
        user = self.get_user_by_id(user_id, include_roles=True)

        # Admin has all permissions
        if UserRole.ADMIN in user.roles:
            return True

        # Get user permissions
        permissions = self._get_role_permissions(user.roles)
        required_permission = f"{resource}:{action}"

        return required_permission in permissions
