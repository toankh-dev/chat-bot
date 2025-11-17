"""API routers package."""

from api.routers.auth_routes import router as auth_router
from api.routers.user_routes import router as user_router
from api.routers.chatbot_routes import router as chatbot_router

__all__ = [
    "auth_router",
    "user_router",
    "chatbot_router",
]
