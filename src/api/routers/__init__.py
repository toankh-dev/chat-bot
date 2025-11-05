"""API routers package."""

from src.api.routers.auth_routes import router as auth_router
from src.api.routers.user_routes import router as user_router
from src.api.routers.chatbot_routes import router as chatbot_router
from src.api.routers.conversation_routes import router as conversation_router

__all__ = [
    "auth_router",
    "user_router",
    "chatbot_router",
    "conversation_router"
]
