"""
User Management API - Using Shared Base
"""

import sys
import os
from fastapi import Depends, HTTPException, status

# Add paths
sys.path.insert(0, '/opt/python')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'common'))

# Import shared base
from utils.fastapi_base import create_management_app

# Import services and models
from common.services.user_service import UserService
from common.models.api.user_models import (
    CreateUserRequest,
    UpdateUserRequest,
    UserStatusUpdate,
    AssignRoleRequest,
    LoginRequest,
    user_to_response
)
from common.utils.exceptions import ValidationError, ForbiddenError
from common.auth.jwt import require_auth, require_permission, get_current_user
from common.models.domain.user import UserStatus

# Create app using shared base
app = create_management_app(
    title="User Management API",
    description="User authentication and management service",
    version="2.0.0"
)

# Initialize service
user_service = UserService()


# ==============================================================================
# Authentication Routes
# ==============================================================================

@app.post("/login", tags=["Authentication"])
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        user, token, permissions = user_service.authenticate(
            email=request.email,
            password=request.password
        )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": user_to_response(user),
            "permissions": permissions
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


# ==============================================================================
# User CRUD Routes
# ==============================================================================

@app.get("/users", tags=["Users"])
async def list_users(
    page: int = 1,
    limit: int = 10,
    group_id: int = None,
    status_filter: str = None,
    current_user: dict = Depends(require_auth)
):
    """List users with pagination"""
    require_permission('user:read')(current_user)

    user_status = UserStatus(status_filter) if status_filter else None
    users, total = user_service.list_users(
        page=page, limit=limit, group_id=group_id, status=user_status
    )

    return {
        "data": [user_to_response(user) for user in users],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.post("/users", tags=["Users"], status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest, current_user: dict = Depends(require_auth)):
    """Create a new user"""
    require_permission('user:create')(current_user)

    user = user_service.create_user(
        email=request.email,
        name=request.name,
        password=request.password,
        group_id=request.group_id,
        is_admin=request.is_admin,
        roles=request.roles
    )

    return {"message": "User created successfully", "data": user_to_response(user)}


@app.get("/users/{user_id}", tags=["Users"])
async def get_user(user_id: int, current_user: dict = Depends(require_auth)):
    """Get user by ID"""
    require_permission('user:read')(current_user)
    user = user_service.get_user_by_id(user_id, include_roles=True)
    return {"data": user_to_response(user)}


@app.put("/users/{user_id}", tags=["Users"])
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: dict = Depends(require_auth)
):
    """Update user information"""
    require_permission('user:update')(current_user)

    user = user_service.update_user(
        user_id=user_id,
        email=request.email,
        name=request.name,
        group_id=request.group_id,
        status=request.status,
        current_user_id=current_user.get('user_id')
    )

    return {"message": "User updated successfully", "data": user_to_response(user)}


@app.delete("/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int, current_user: dict = Depends(require_auth)):
    """Delete user"""
    require_permission('user:delete')(current_user)
    user_service.delete_user(user_id, current_user.get('user_id'))
    return {"message": "User deleted successfully"}


# ==============================================================================
# Role Management
# ==============================================================================

@app.post("/users/{user_id}/roles", tags=["Roles"])
async def assign_role(
    user_id: int,
    request: AssignRoleRequest,
    current_user: dict = Depends(require_auth)
):
    """Assign role to user"""
    require_permission('user:manage')(current_user)
    assigned = user_service.assign_role(user_id, request.role)

    message = f"Role {request.role} assigned to user" if assigned else f"User already has role {request.role}"
    return {"message": message}


@app.delete("/users/{user_id}/roles/{role_name}", tags=["Roles"])
async def remove_role(user_id: int, role_name: str, current_user: dict = Depends(require_auth)):
    """Remove role from user"""
    require_permission('user:manage')(current_user)
    removed = user_service.remove_role(user_id, role_name)

    if not removed:
        raise HTTPException(status_code=404, detail=f"User does not have role {role_name}")

    return {"message": f"Role {role_name} removed from user"}


# ==============================================================================
# Current User
# ==============================================================================

@app.get("/me", tags=["Current User"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    user = user_service.get_user_by_id(current_user.get('user_id'), include_roles=True)
    return {"data": user_to_response(user)}


@app.put("/me", tags=["Current User"])
async def update_current_user(request: UpdateUserRequest, current_user: dict = Depends(get_current_user)):
    """Update current user information"""
    user_id = current_user.get('user_id')
    user = user_service.update_user(
        user_id=user_id,
        email=request.email,
        name=request.name,
        current_user_id=user_id
    )
    return {"message": "Profile updated successfully", "data": user_to_response(user)}
