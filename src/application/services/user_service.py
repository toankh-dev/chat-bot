"""
User service.

Handles user management business logic.
"""

from typing import List, Optional
import bcrypt
from domain.value_objects.email import Email
from core.errors import NotFoundError, ValidationError, ResourceConflictError
from domain.entities.user import User
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository
from shared.interfaces.repositories.user_repository import UserRepository
from shared.interfaces.repositories.group_chatbot_repository import GroupChatbotRepository
from shared.interfaces.repositories.user_chatbot_repository import UserChatbotRepository


class UserService:
    """
    Service for user management operations.

    Works exclusively with domain entities, not ORM models.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_group_repository: Optional[UserGroupRepository] = None,
        group_repository: Optional[GroupRepository] = None,
        group_chatbot_repository: Optional[GroupChatbotRepository] = None,
        user_chatbot_repository: Optional[UserChatbotRepository] = None
    ):
        self.user_repository = user_repository
        self.user_group_repository = user_group_repository
        self.group_repository = group_repository
        self.group_chatbot_repository = group_chatbot_repository
        self.user_chatbot_repository = user_chatbot_repository

    async def get_user_by_id(self, user_id: int, include_groups: bool = True) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID (integer)
            include_groups: Whether to load user's groups

        Returns:
            User: Found user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Load groups if requested
        if include_groups and self.user_group_repository:
            groups = await self.user_group_repository.get_user_groups(user_id)
            # Attach groups to user object for response
            user.groups = groups

        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        List all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[User]: List of users
        """
        return await self.user_repository.find_all(skip=skip, limit=limit)

    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        is_admin: bool = False,
        group_ids: Optional[List[int]] = None,
        added_by: Optional[int] = None
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            password: Plain password
            name: User full name
            is_admin: Whether user is admin
            group_ids: Optional list of group IDs to assign user to
            added_by: User ID of admin creating this user

        Returns:
            User: Created user

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        if not email or not email.strip():
            raise ValidationError("Email is required")

        if not password or not password.strip():
            raise ValidationError("Password is required")

        if not name or not name.strip():
            raise ValidationError("Name is required")

        # Validate password strength
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long")

        # Additional password complexity validation
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")

        # Check email uniqueness
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValidationError("Email already registered")

        # Validate group IDs if provided
        if group_ids:
            # added_by is required when assigning groups
            if not added_by:
                raise ValidationError("added_by is required when assigning groups")

            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Create domain entity
        # ID will be set by database auto-increment
        user = User(
            id=0,  # Temporary ID, will be set by database
            email=Email(email),
            username=email.split('@')[0],  # Derive username from email
            full_name=name.strip(),
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=is_admin
        )

        created_user = await self.user_repository.create(user)

        # Assign to groups if provided
        # Note: added_by has already been validated above if group_ids are provided
        if group_ids and self.user_group_repository:
            await self.user_group_repository.assign_user_to_groups(
                user_id=created_user.id,
                group_ids=group_ids,
                added_by=added_by  # added_by is validated to be not None when group_ids is not empty
            )

        return created_user

    async def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        group_ids: Optional[List[int]] = None,
        updated_by: Optional[int] = None
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            name: New name (optional)
            is_active: Active status (optional)
            status: New status (optional)
            group_ids: New list of group IDs (replaces existing, optional)
            updated_by: User ID of admin updating this user

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If invalid status or group IDs
        """
        user = await self.get_user_by_id(user_id)

        # Validate name if provided
        if name is not None:
            if not name or not name.strip():
                raise ValidationError("Name cannot be empty")

        # Validate admin deactivation
        if is_active is not None and not is_active and user.is_superuser:
            # Check if this is the only admin or the first admin
            first_admin = await self._get_first_admin()

            # Prevent deactivating the first admin
            if user_id == first_admin.id:
                raise ValidationError("Cannot deactivate the account creator")

            # Check if there are other active admins
            from sqlalchemy import select, func
            from infrastructure.postgresql.models.user_model import UserModel

            if hasattr(self.user_repository, 'session'):
                result = await self.user_repository.session.execute(
                    select(func.count(UserModel.id))
                    .where(UserModel.is_admin == True)
                    .where(UserModel.status == 'active')
                    .where(UserModel.id != user_id)
                )
                active_admin_count = result.scalar()

                if active_admin_count == 0:
                    raise ValidationError("Cannot deactivate the last active admin account")

        # Update domain entity using its methods
        if name is not None:
            # Update the full_name attribute directly (domain entity doesn't have .name)
            user = User(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=name.strip(),
                hashed_password=user.hashed_password,
                is_active=user.is_active if is_active is None else is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        elif is_active is not None:
            if is_active:
                user.activate()
            else:
                user.deactivate()

        updated_user = await self.user_repository.update(user)

        # Update group assignments if provided
        if group_ids is not None:
            # updated_by is required when updating group assignments
            if not updated_by:
                raise ValidationError("updated_by is required when updating group assignments")

            # Validate group IDs
            if self.group_repository:
                for group_id in group_ids:
                    if not await self.group_repository.exists(group_id):
                        raise ValidationError(f"Group with ID {group_id} not found")

            if self.user_group_repository:
                # Use the user_id parameter directly (it's already an integer from the API)
                await self.user_group_repository.assign_user_to_groups(
                    user_id=user_id,
                    group_ids=group_ids,
                    added_by=updated_by
                )

        return updated_user

    async def delete_user(self, user_id: int, deleted_by: int) -> bool:
        """
        Delete user.

        Args:
            user_id: User ID (integer)
            deleted_by: User ID of admin performing the deletion

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If user not found
            ValidationError: If trying to delete self or admin account
            ResourceConflictError: If user cannot be deleted due to foreign key constraints
        """
        if not await self.user_repository.exists(user_id):
            raise NotFoundError(f"User with ID {user_id} not found")

        # Prevent self-deletion
        if user_id == deleted_by:
            raise ValidationError("You cannot delete your own account")

        # Get the user to check if they're an admin
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Prevent deletion of admin accounts
        if user.is_superuser:
            # Find the first admin (user with ID 1 or lowest admin ID)
            first_admin = await self._get_first_admin()

            # Only the first admin can delete other admins
            if deleted_by != first_admin.id:
                raise ValidationError("Only the account creator can delete admin accounts")

            # Even the first admin cannot delete themselves
            if user_id == first_admin.id:
                raise ValidationError("The account creator cannot be deleted")

        # Check for foreign key constraints that would prevent deletion
        conflict_reasons = []

        # Check if user is a member of any groups (user_groups.user_id)
        # Even though DB has CASCADE, we prevent deletion as a business rule
        if self.user_group_repository:
            try:
                from sqlalchemy import select
                from infrastructure.postgresql.models.user_group_model import UserGroup as UserGroupModel

                # Access the session from user_group_repository if it's the implementation
                if hasattr(self.user_group_repository, 'session'):
                    # Check if user is a member of any groups
                    result = await self.user_group_repository.session.execute(
                        select(UserGroupModel).where(UserGroupModel.user_id == user_id).limit(1)
                    )
                    if result.scalar_one_or_none():
                        conflict_reasons.append("user is assigned to groups")

                    # Check if user has added other users to groups (user_groups.added_by)
                    result = await self.user_group_repository.session.execute(
                        select(UserGroupModel).where(UserGroupModel.added_by == user_id).limit(1)
                    )
                    if result.scalar_one_or_none():
                        conflict_reasons.append("user has added other users to groups")
            except Exception:
                pass

        # Check if user has assigned chatbots to groups (group_chatbots.assigned_by)
        if self.group_chatbot_repository:
            try:
                from sqlalchemy import select
                from infrastructure.postgresql.models.group_chatbot import GroupChatbotModel

                if hasattr(self.group_chatbot_repository, 'session'):
                    result = await self.group_chatbot_repository.session.execute(
                        select(GroupChatbotModel).where(GroupChatbotModel.assigned_by == user_id).limit(1)
                    )
                    if result.scalar_one_or_none():
                        conflict_reasons.append("user has assigned chatbots to groups")
            except Exception:
                pass

        # Check if user has assigned chatbots to users (user_chatbots.assigned_by)
        if self.user_chatbot_repository:
            try:
                from sqlalchemy import select
                from infrastructure.postgresql.models.user_chatbot import UserChatbotModel

                if hasattr(self.user_chatbot_repository, 'session'):
                    result = await self.user_chatbot_repository.session.execute(
                        select(UserChatbotModel).where(UserChatbotModel.assigned_by == user_id).limit(1)
                    )
                    if result.scalar_one_or_none():
                        conflict_reasons.append("user has assigned chatbots to users")
            except Exception:
                pass

        if conflict_reasons:
            reason_text = ", ".join(conflict_reasons)
            raise ResourceConflictError(
                f"Cannot delete user: {reason_text}. Please reassign these relationships to another user first."
            )

        return await self.user_repository.delete(user_id)

    async def _get_first_admin(self) -> User:
        """
        Get the first admin user (account creator).

        Returns:
            User: The first admin user in the system

        Raises:
            NotFoundError: If no admin users exist
        """
        # Get all admin users ordered by ID (first created)
        from sqlalchemy import select
        from infrastructure.postgresql.models.user_model import UserModel

        if hasattr(self.user_repository, 'session'):
            result = await self.user_repository.session.execute(
                select(UserModel)
                .where(UserModel.is_admin == True)
                .order_by(UserModel.id.asc())
                .limit(1)
            )
            first_admin_model = result.scalar_one_or_none()

            if not first_admin_model:
                raise NotFoundError("No admin users found in the system")

            # Convert to entity
            from infrastructure.postgresql.mappers.user_mapper import UserMapper
            mapper = UserMapper()
            return mapper.to_entity(first_admin_model)

        # Fallback: just get by ID 1
        first_admin = await self.user_repository.find_by_id(1)
        if not first_admin or not first_admin.is_superuser:
            raise NotFoundError("First admin user not found")

        return first_admin

    async def update_own_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """
        Update user's own profile.

        Args:
            user_id: User ID
            name: New name (optional)
            email: New email (optional)

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails
        """
        user = await self.get_user_by_id(user_id)

        # Validate name if provided
        if name is not None:
            if not name or not name.strip():
                raise ValidationError("Name cannot be empty")

        # Validate email if provided
        if email is not None:
            if not email or not email.strip():
                raise ValidationError("Email cannot be empty")

        # Check if email is being changed and if it already exists
        if email is not None and str(user.email) != email:
            existing_user = await self.user_repository.find_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ValidationError("Email already registered")

            # Update email
            user = User(
                id=user.id,
                email=Email(email),
                username=email.split('@')[0],  # Update username from email
                full_name=name.strip() if name is not None else user.full_name,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        elif name is not None:
            # Only update name
            user = User(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=name.strip(),
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        else:
            # No changes
            return user

        return await self.user_repository.update(user)

    async def change_own_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Change user's own password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New plain password

        Raises:
            NotFoundError: If user not found
            ValidationError: If validation fails
        """
        user = await self.get_user_by_id(user_id)

        # Validate passwords
        if not current_password or not current_password.strip():
            raise ValidationError("Current password is required")

        if not new_password or not new_password.strip():
            raise ValidationError("New password is required")

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            raise ValidationError("Current password is incorrect")

        # Validate new password strength
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters long")

        if not any(c.isupper() for c in new_password):
            raise ValidationError("New password must contain at least one uppercase letter")

        if not any(c.islower() for c in new_password):
            raise ValidationError("New password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in new_password):
            raise ValidationError("New password must contain at least one digit")

        # Check if new password is same as current
        if current_password == new_password:
            raise ValidationError("New password must be different from current password")

        # Hash new password
        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Update password
        user = User(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        await self.user_repository.update(user)

    async def change_password(self, user_id: int, new_password: str) -> User:
        """
        Change user password (admin operation).

        Args:
            user_id: User ID
            new_password: New plain password

        Returns:
            User: Updated user domain entity

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user_by_id(user_id)

        # Hash new password
        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Update password
        user = User(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return await self.user_repository.update(user)
