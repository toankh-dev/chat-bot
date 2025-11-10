from fastapi import APIRouter
from api.controllers.ai_controller import AIController

def create_ai_routes() -> APIRouter:
    """Create unified AI routes (RAG + LLM)."""
    ai_controller = AIController()
    return ai_controller.router