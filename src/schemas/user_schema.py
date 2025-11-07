"""User request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
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
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)
    is_admin: bool = False
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign user to")


class UserUpdate(BaseModel):
    """User update request."""
    name: Optional[str] = None
    status: Optional[str] = None
    group_ids: Optional[List[int]] = Field(default=None, description="List of group IDs to assign user to (replaces existing)")


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
