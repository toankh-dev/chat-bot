"""Document routes."""

from fastapi import APIRouter, status
from api.controllers.document_controller import (
    upload_document,
    delete_document,
    list_documents,
    process_document,
    get_document_status
)
from schemas.document_schema import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentProcessingResponse
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

router.add_api_route(
    "/documents/{document_id}/process",
    process_document,
    methods=["POST"],
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Process document",
    description="Process an uploaded document: extract text, chunk, and add to Knowledge Base"
)

router.add_api_route(
    "/documents/{document_id}/status",
    get_document_status,
    methods=["GET"],
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document status",
    description="Get processing status of a document"
)
