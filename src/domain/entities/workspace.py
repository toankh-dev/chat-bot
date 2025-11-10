"""
Workspace domain entity.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional
from ..value_objects.uuid_vo import UUID


@dataclass
class WorkspaceEntity:
    """
    Workspace entity for organizing chatbots and users.

    A workspace provides isolation and organization for groups of chatbots
    and their associated users.

    Attributes:
        id: Unique workspace identifier
        name: Workspace name
        description: Workspace description
        owner_id: User ID of workspace owner
        is_active: Whether workspace is active
        settings: Workspace-specific settings
        created_at: Workspace creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    name: str
    description: str
    owner_id: UUID
    is_active: bool = True
    settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Validate workspace invariants."""
        if len(self.name) < 3:
            raise ValueError("Workspace name must be at least 3 characters")

    def deactivate(self) -> None:
        """Deactivate workspace."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate workspace."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def update_settings(self, settings: dict) -> None:
        """Update workspace settings."""
        self.settings.update(settings)
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "owner_id": str(self.owner_id),
            "is_active": self.is_active,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# Backwards compatibility alias
Workspace = WorkspaceEntity
