"""Document routes."""

from fastapi import APIRouter, status
from api.controllers.document_controller import (
    upload_document,
    delete_document,
    list_documents,
)
from schemas.document_schema import (
    DocumentUploadResponse,
    DocumentListResponse
)

router = APIRouter()

router.add_api_route(
    "/documents/upload",
    upload_document,
    methods=["POST"],
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload document",
    description="Upload a document file"
)

router.add_api_route(
    "/documents/{document_id}",
    delete_document,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
    summary="Delete document",
    description="Delete a document"
)

router.add_api_route(
    "/documents/",
    list_documents,
    methods=["GET"],
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List documents",
    description="List user documents"
)