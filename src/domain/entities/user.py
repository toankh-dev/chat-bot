"""
User domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional
from ..value_objects.email import Email


@dataclass
class UserEntity:
    """
    User entity representing a system user.

    Attributes:
        id: Unique user identifier (integer)
        email: User email address
        username: Unique username
        full_name: User's full name
        hashed_password: Bcrypt hashed password
        is_active: Whether user account is active
        is_superuser: Whether user has superuser privileges
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login_at: Last login timestamp
    """

    id: int
    email: Email
    username: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_login_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.full_name) < 1:
            raise ValueError("Full name is required")

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def record_login(self) -> None:
        """Record user login event."""
        self.last_login_at = datetime.now(UTC)

    def update_password(self, new_hashed_password: str) -> None:
        """Update user password."""
        self.hashed_password = new_hashed_password
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": str(self.email),
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
 

# Backwards compatibility alias
User = UserEntity
