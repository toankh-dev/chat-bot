"""Permission and Role domain models for RBAC"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class PermissionAction(str, Enum):
    """Permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class PermissionResource(str, Enum):
    """Permission resources"""
    USER = "user"
    GROUP = "group"
    CHATBOT = "chatbot"
    CONVERSATION = "conversation"
    TOOL = "tool"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class Permission(BaseModel):
    """Permission domain model"""
    id: Optional[int] = None
    resource: PermissionResource
    action: PermissionAction
    description: Optional[str] = None

    @property
    def code(self) -> str:
        """Permission code (e.g., 'chatbot:create')"""
        return f"{self.resource.value}:{self.action.value}"

    class Config:
        use_enum_values = True


class Role(BaseModel):
    """Role domain model"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    is_system_role: bool = False  # System roles cannot be deleted
    created_at: Optional[datetime] = None

    # Relationships (populated when needed)
    permissions: List[Permission] = Field(default_factory=list)
    permission_codes: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserRoleAssignment(BaseModel):
    """User-Role assignment"""
    user_id: int
    role_id: int
    assigned_by: int
    assigned_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
