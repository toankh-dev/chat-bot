from fastapi import APIRouter, status
from api.controllers.auth_controller import login, register, logout, refresh_token
from schemas.auth_schema import LoginResponse

router = APIRouter()

router.add_api_route(
    "/login",
    login,
    methods=["POST"],
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and return JWT tokens"
)

router.add_api_route(
    "/register",
    register,
    methods=["POST"],
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register new user and return JWT tokens"
)

router.add_api_route(
    "/refresh",
    refresh_token,
    methods=["POST"],
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh access token using a valid refresh token"
)

router.add_api_route(
    "/logout",
    logout,
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout current user (client should discard the JWT token)"
)
