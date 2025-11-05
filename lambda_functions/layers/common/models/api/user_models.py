"""API request/response models for user endpoints"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from ..domain.user import UserStatus, UserRole


# Request Models

class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    group_id: Optional[int] = None
    is_admin: bool = False
    roles: Optional[List[str]] = Field(default_factory=lambda: ['user'])


class UpdateUserRequest(BaseModel):
    """Request model for updating a user"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    group_id: Optional[int] = None
    status: Optional[UserStatus] = None


class UserStatusUpdate(BaseModel):
    """Request model for updating user status"""
    status: UserStatus


class AssignRoleRequest(BaseModel):
    """Request model for assigning a role"""
    role: str


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str


# Response Models

class UserResponse(BaseModel):
    """Response model for a single user"""
    id: int
    email: str
    name: str
    group_id: Optional[int]
    is_admin: bool
    status: UserStatus
    roles: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserListResponse(BaseModel):
    """Response model for user list"""
    users: List[UserResponse]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


class LoginResponse(BaseModel):
    """Response model for login"""
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse
    permissions: List[str]


class UserCreatedResponse(BaseModel):
    """Response model for user creation"""
    id: int
    email: str
    name: str
    message: str = "User created successfully"


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# Helper functions

def user_to_response(user) -> dict:
    """Convert User domain model to UserResponse dict"""
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'group_id': user.group_id,
        'is_admin': user.is_admin,
        'status': user.status.value,
        'roles': [role.value for role in user.roles] if user.roles else [],
        'created_at': user.created_at,
        'updated_at': user.updated_at
    }
