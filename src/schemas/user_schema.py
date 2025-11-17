from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


class GroupInUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)
    is_admin: bool = False
    group_ids: Optional[List[int]] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
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
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    is_active: Optional[bool] = None
    group_ids: Optional[List[int]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v.strip() if v else None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Name cannot be empty")
        return v.strip() if v else None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
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
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    is_admin: bool
    status: str
    created_at: datetime
    updated_at: datetime
    groups: Optional[List[GroupInUser]] = None

    @field_validator('email', mode='before')
    @classmethod
    def validate_email(cls, v):
        if hasattr(v, 'value'):
            return str(v)
        return v
