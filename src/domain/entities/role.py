"""
Role domain entity for RBAC.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Set
from ..value_objects.uuid_vo import UUID


@dataclass
class RoleEntity:
    """
    Role entity for role-based access control.

    Attributes:
        id: Unique role identifier
        name: Role name (e.g., 'admin', 'user', 'viewer')
        description: Role description
        permissions: Set of permission strings
        created_at: Role creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Common permission constants
    PERM_USER_READ = "user:read"
    PERM_USER_WRITE = "user:write"
    PERM_USER_DELETE = "user:delete"

    PERM_WORKSPACE_READ = "workspace:read"
    PERM_WORKSPACE_WRITE = "workspace:write"
    PERM_WORKSPACE_DELETE = "workspace:delete"

    PERM_CHATBOT_READ = "chatbot:read"
    PERM_CHATBOT_WRITE = "chatbot:write"
    PERM_CHATBOT_DELETE = "chatbot:delete"
    PERM_CHATBOT_EXECUTE = "chatbot:execute"

    PERM_CONVERSATION_READ = "conversation:read"
    PERM_CONVERSATION_WRITE = "conversation:write"
    PERM_CONVERSATION_DELETE = "conversation:delete"

    PERM_ADMIN = "admin:all"

    def __post_init__(self):
        """Validate role invariants."""
        if len(self.name) < 2:
            raise ValueError("Role name must be at least 2 characters")

    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        self.permissions.add(permission)
        self.updated_at = datetime.now(UTC)

    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        self.permissions.discard(permission)
        self.updated_at = datetime.now(UTC)

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions or self.PERM_ADMIN in self.permissions

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# Backwards compatibility alias
Role = RoleEntity