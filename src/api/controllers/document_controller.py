"""Document Controller - Document management endpoints."""

from fastapi import Depends, HTTPException, UploadFile, File, Form, status
from schemas.document_schema import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentProcessingResponse,
    DocumentDeleteResponse
)
from usecases.document_use_cases import (
    UploadDocumentUseCase,
    DeleteDocumentUseCase,
    ListUserDocumentsUseCase,
    ProcessDocumentUseCase,
    GetDocumentStatusUseCase
)
from core.dependencies import (
    get_upload_document_use_case,
    get_delete_document_use_case,
    get_list_user_documents_use_case,
    get_process_document_use_case,
    get_document_status_use_case
)
from api.middlewares.jwt_middleware import get_current_user
from domain.entities.user import UserEntity
from core.logger import logger


# ============================================================================
# Document Controller Functions
# ============================================================================

async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(...),
    current_user: UserEntity = Depends(get_current_user),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case)
) -> DocumentUploadResponse:
    """
    Upload a document file.

    Args:
        file: File to upload
        domain: Domain classification
        current_user: Authenticated user from JWT token
        use_case: Upload document use case instance

    Returns:
        DocumentUploadResponse: Upload response with document info
    """
    try:
        user_id = str(current_user.id.value)
        logger.info(f"Uploading document: {file.filename}, domain: {domain}, user: {user_id}")

        document = await use_case.execute(
            file_content=file.file,
            filename=file.filename,
            content_type=file.content_type,
            user_id=user_id,
            domain=domain
        )

        return DocumentUploadResponse(
            id=str(document.id.value),
            filename=document.filename,
            file_size=document.file_size,
            domain=document.domain,
            upload_status=document.upload_status,
            uploaded_at=document.uploaded_at
        )

    except ValueError as e:
        logger.error(f"Upload validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


async def delete_document(
    document_id: str,
    current_user: UserEntity = Depends(get_current_user),
    use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case)
) -> DocumentDeleteResponse:
    """
    Delete a document.

    Args:
        document_id: Document ID to delete
        current_user: Authenticated user from JWT token
        use_case: Delete document use case instance

    Returns:
        DocumentDeleteResponse: Success message
    """
    try:
        user_id = str(current_user.id.value)
        logger.info(f"Deleting document: {document_id}, user: {user_id}")

        success = await use_case.execute(document_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return DocumentDeleteResponse(message="Document deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete failed"
        )


async def list_documents(
    current_user: UserEntity = Depends(get_current_user),
    domain: str = None,
    skip: int = 0,
    limit: int = 100,
    use_case: ListUserDocumentsUseCase = Depends(get_list_user_documents_use_case)
) -> DocumentListResponse:
    """
    List user documents.

    Args:
        current_user: Authenticated user from JWT token
        domain: Optional domain filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        use_case: List documents use case instance

    Returns:
        DocumentListResponse: List of documents
    """
    try:
        user_id = str(current_user.id.value)
        logger.info(f"Listing documents for user: {user_id}, domain: {domain}")

        documents = await use_case.execute(user_id, domain, skip, limit)

        document_responses = [
            DocumentUploadResponse(
                id=str(doc.id.value),
                filename=doc.filename,
                file_size=doc.file_size,
                domain=doc.domain,
                upload_status=doc.upload_status,
                uploaded_at=doc.uploaded_at
            )
            for doc in documents
        ]

        return DocumentListResponse(
            documents=document_responses,
            total=len(document_responses)
        )

    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


async def process_document(
    document_id: str,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ProcessDocumentUseCase = Depends(get_process_document_use_case)
) -> DocumentProcessingResponse:
    """
    Process an uploaded document: extract text, chunk, and add to Knowledge Base.

    Args:
        document_id: Document ID to process
        current_user: Authenticated user from JWT token
        use_case: Process document use case instance

    Returns:
        DocumentProcessingResponse: Processing result
    """
    try:
        user_id = str(current_user.id.value)
        logger.info(f"Processing document: {document_id}, user: {user_id}")

        result = await use_case.execute(document_id, user_id)
        return DocumentProcessingResponse(**result)

    except ValueError as e:
        logger.error(f"Process validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Process document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed"
        )


async def get_document_status(
    document_id: str,
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetDocumentStatusUseCase = Depends(get_document_status_use_case)
) -> DocumentStatusResponse:
    """
    Get processing status of a document.

    Args:
        document_id: Document ID
        current_user: Authenticated user from JWT token
        use_case: Get document status use case instance

    Returns:
        DocumentStatusResponse: Document status
    """
    try:
        user_id = str(current_user.id.value)
        logger.info(f"Getting status for document: {document_id}, user: {user_id}")

        document = await use_case.execute(document_id, user_id)
        return DocumentStatusResponse(
            id=str(document.id.value),
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            knowledge_base_id=document.knowledge_base_id,
            error_message=document.error_message,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at
        )

    except ValueError as e:
        logger.error(f"Document not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get status"
        )
