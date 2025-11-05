"""User request/response schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)
    is_admin: bool = False


class UserUpdate(BaseModel):
    """User update request."""
    name: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    name: str
    is_admin: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
