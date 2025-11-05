"""User domain model"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"              # Full system access
    GROUP_ADMIN = "group_admin"  # Manage own group
    USER = "user"                 # Regular user


class User(BaseModel):
    """User domain model"""
    id: Optional[int] = None
    group_id: Optional[int] = None
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    is_admin: bool = False
    status: UserStatus = UserStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationships (populated when needed)
    roles: List[UserRole] = Field(default_factory=list)
    group_name: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserProfile(BaseModel):
    """Public user profile (safe to expose)"""
    id: int
    name: str
    email: EmailStr
    status: UserStatus
    is_admin: bool
    group_name: Optional[str] = None
    created_at: datetime

    class Config:
        use_enum_values = True
