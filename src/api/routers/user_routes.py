"""User routes."""

from fastapi import APIRouter, status
from typing import List
from api.controllers.user_controller import (
    get_current_user_profile,
    list_users,
    get_user,
    create_user,
    update_user,
    delete_user,
    update_own_profile,
    change_password
)
from schemas.user_schema import UserResponse

router = APIRouter()

router.add_api_route(
    "/me",
    get_current_user_profile,
    methods=["GET"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get authenticated user's profile information"
)

router.add_api_route(
    "/me",
    update_own_profile,
    methods=["PATCH"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update own profile",
    description="Update authenticated user's profile information (name, email)"
)

router.add_api_route(
    "/me/password",
    change_password,
    methods=["PUT"],
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change authenticated user's password"
)

router.add_api_route(
    "/",
    list_users,
    methods=["GET"],
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List users",
    description="List all users (admin only)"
)

router.add_api_route(
    "/{user_id}",
    get_user,
    methods=["GET"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Get user details by ID (admin only)"
)

router.add_api_route(
    "/",
    create_user,
    methods=["POST"],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create new user (admin only)"
)

router.add_api_route(
    "/{user_id}",
    update_user,
    methods=["PATCH"],
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user information (admin only)"
)

router.add_api_route(
    "/{user_id}",
    delete_user,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user (admin only)"
)
