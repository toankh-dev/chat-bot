from fastapi import APIRouter
from api.controllers.document_controller import DocumentController

router = APIRouter()

# Document controller instance
document_controller = DocumentController()

# Include document routes
router.include_router(document_controller.router)