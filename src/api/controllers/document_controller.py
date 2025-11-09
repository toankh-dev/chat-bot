from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from schemas.document_schema import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentProcessingResponse
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
from core.logger import logger

class DocumentController:
    def __init__(self):
        self.router = APIRouter(prefix="/documents", tags=["Documents"])
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.post("/upload", response_model=DocumentUploadResponse)
        async def upload_document(
            file: UploadFile = File(...),
            domain: str = Form(...),
            user_id: str = Form(...),  # In real app, get from JWT token
            use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case)
        ):
            try:
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
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Upload error: {e}")
                raise HTTPException(status_code=500, detail="Upload failed")
        
        @self.router.delete("/{document_id}")
        async def delete_document(
            document_id: str,
            user_id: str = Form(...),  # In real app, get from JWT token
            use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case)
        ):
            try:
                success = await use_case.execute(document_id, user_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Document not found")
                return {"message": "Document deleted successfully"}
            except Exception as e:
                logger.error(f"Delete error: {e}")
                raise HTTPException(status_code=500, detail="Delete failed")
        
        @self.router.get("/", response_model=DocumentListResponse)
        async def list_documents(
            user_id: str,  # In real app, get from JWT token
            domain: str = None,
            skip: int = 0,
            limit: int = 100,
            use_case: ListUserDocumentsUseCase = Depends(get_list_user_documents_use_case)
        ):
            try:
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
                raise HTTPException(status_code=500, detail="Failed to list documents")

        @self.router.post("/{document_id}/process", response_model=DocumentProcessingResponse)
        async def process_document(
            document_id: str,
            user_id: str = Form(...),  # In real app, get from JWT token
            use_case: ProcessDocumentUseCase = Depends(get_process_document_use_case)
        ):
            """
            Process an uploaded document: extract text, chunk, and add to Knowledge Base.
            """
            try:
                result = await use_case.execute(document_id, user_id)
                return DocumentProcessingResponse(**result)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Process document error: {e}")
                raise HTTPException(status_code=500, detail="Processing failed")

        @self.router.get("/{document_id}/status", response_model=DocumentStatusResponse)
        async def get_document_status(
            document_id: str,
            user_id: str,  # In real app, get from JWT token
            use_case: GetDocumentStatusUseCase = Depends(get_document_status_use_case)
        ):
            """
            Get processing status of a document.
            """
            try:
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
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Get status error: {e}")
                raise HTTPException(status_code=500, detail="Failed to get status")