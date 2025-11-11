"""User request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


class GroupInUser(BaseModel):
    """Group information in user response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters, contain uppercase, lowercase, and digit")
    name: str = Field(..., min_length=1, description="User's full name")
    is_admin: bool = False
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign user to")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserUpdate(BaseModel):
    """User update request (admin only)."""
    name: Optional[str] = Field(default=None, min_length=1, description="User's full name")
    is_active: Optional[bool] = None
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign user to (replaces existing)")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v.strip() if v else None


class UserProfileUpdate(BaseModel):
    """User profile update request (for logged-in user)."""
    name: Optional[str] = Field(default=None, min_length=1, description="User's full name")
    email: Optional[EmailStr] = Field(default=None, description="User's email address")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v.strip() if v else None


class ChangePasswordRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=6, description="Current password for verification")
    new_password: str = Field(..., min_length=6, description="New password must contain uppercase, lowercase, and digit")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password meets strength requirements."""
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("New password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    """User response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    is_admin: bool
    status: str
    created_at: datetime
    updated_at: datetime
    groups: Optional[List[GroupInUser]] = Field(default=None, description="Groups the user belongs to")
