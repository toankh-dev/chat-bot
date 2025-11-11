"""
User domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
        name: User's name
        password_hash: Bcrypt hashed password
        status: User account status (active/inactive)
        is_admin: Whether user has admin privileges
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login_at: Last login timestamp
    """

    id: Optional[int]
    email: Email
    username: str
    name: str
    password_hash: str
    status: str = "active"
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.name) < 1:
            raise ValueError("Name is required")

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.status = "inactive"
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate user account."""
        self.status = "active"
        self.updated_at = datetime.now()

    def record_login(self) -> None:
        """Record user login event."""
        self.last_login_at = datetime.now()

    def update_password(self, new_password_hash: str) -> None:
        """Update user password."""
        self.password_hash = new_password_hash
        self.updated_at = datetime.now()

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == "active"

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": str(self.email),
            "username": self.username,
            "name": self.name,
            "status": self.status,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
 

# Backwards compatibility alias
User = UserEntity
