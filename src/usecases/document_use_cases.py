from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from shared.interfaces.repositories.document_repository import DocumentRepository
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from application.services.document_processing_service import DocumentProcessingService
from application.services.document_chunking_service import DocumentChunkingService
from application.services.kb_sync_service import KBSyncService
from typing import List, Dict, Any
from domain.entities.document import DocumentEntity

class UploadDocumentUseCase:
    def __init__(self, document_upload_service: IDocumentUploadService):
        self.document_upload_service = document_upload_service
    
    async def execute(self, file_content, filename: str, content_type: str, 
                     user_id: str, domain: str) -> DocumentEntity:
        return await self.document_upload_service.upload_document(
            file_content, filename, content_type, user_id, domain
        )

class DeleteDocumentUseCase:
    def __init__(self, document_upload_service: IDocumentUploadService):
        self.document_upload_service = document_upload_service
    
    async def execute(self, document_id: str, user_id: str) -> bool:
        return await self.document_upload_service.delete_document(document_id, user_id)

class ListUserDocumentsUseCase:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, user_id: str, domain: str = None, skip: int = 0, limit: int = 100) -> List[DocumentEntity]:
        if domain:
            return await self.document_repository.find_by_user_and_domain(user_id, domain, skip, limit)
        # If no domain specified, would need a find_by_user method
        return []


class ProcessDocumentUseCase:
    """Use case for processing uploaded documents and adding them to Knowledge Base."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        file_storage_service: IFileStorageService,
        processing_service: DocumentProcessingService,
        chunking_service: DocumentChunkingService,
        kb_sync_service: KBSyncService,
        kb_config: Dict[str, str]
    ):
        self.document_repository = document_repository
        self.file_storage_service = file_storage_service
        self.processing_service = processing_service
        self.chunking_service = chunking_service
        self.kb_sync_service = kb_sync_service
        self.kb_config = kb_config

    async def execute(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process a document: extract text, chunk, embed, and add to KB.

        Args:
            document_id: ID of the document to process
            user_id: ID of the user (for authorization)

        Returns:
            Dictionary with processing results

        Raises:
            ValueError: If document not found or user not authorized
        """
        # Get document from database
        document = await self.document_repository.find_by_id(document_id)

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.user_id != user_id:
            raise ValueError("User not authorized to process this document")

        if document.upload_status != "uploaded":
            raise ValueError(f"Document cannot be processed: status is {document.upload_status}")

        try:
            # Step 1: Download file from S3
            file_content = await self.file_storage_service.download_file(document.s3_key)

            if not file_content:
                raise ValueError("Failed to download file from storage")

            # Step 2: Extract text from file
            text = await self.processing_service.extract_text(
                file_content=file_content,
                filename=document.filename,
                content_type=document.content_type
            )

            # Validate extracted text
            if not self.processing_service.validate_extracted_text(text):
                raise ValueError("Extracted text is too short or empty")

            text_stats = self.processing_service.get_text_statistics(text)

            # Step 3: Chunk the text
            chunks = await self.chunking_service.chunk_text(
                text=text,
                document_id=str(document.id),
                filename=document.filename,
                domain=document.domain,
                metadata={
                    "user_id": document.user_id,
                    "content_type": document.content_type,
                    "file_size": document.file_size
                }
            )

            chunk_stats = self.chunking_service.get_chunking_statistics(chunks)

            # Step 4: Get Knowledge Base ID for domain
            kb_id = self.kb_sync_service.get_kb_id_for_domain(
                domain=document.domain,
                kb_config=self.kb_config
            )

            # Step 5: Add chunks to Knowledge Base
            sync_result = await self.kb_sync_service.add_document_to_kb(
                document=document,
                chunks=chunks,
                knowledge_base_id=kb_id
            )

            return {
                **sync_result,
                "text_statistics": text_stats,
                "chunk_statistics": chunk_stats
            }

        except Exception as e:
            # Mark document as failed
            document.mark_as_failed(str(e))
            await self.document_repository.update(document)

            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }


class GetDocumentStatusUseCase:
    """Use case for getting document processing status."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: str, user_id: str) -> DocumentEntity:
        """
        Get document status.

        Args:
            document_id: ID of the document
            user_id: ID of the user (for authorization)

        Returns:
            Document entity

        Raises:
            ValueError: If document not found or user not authorized
        """
        document = await self.document_repository.find_by_id(document_id)

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.user_id != user_id:
            raise ValueError("User not authorized to access this document")

        return document