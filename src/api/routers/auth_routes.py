"""Authentication routes."""

from fastapi import APIRouter, status
from src.api.controllers.auth_controller import login, register
from src.schemas.auth_schema import LoginResponse

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
