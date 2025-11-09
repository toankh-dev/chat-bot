"""
Document Processing Pipeline Service - Orchestrate document processing flow.
"""

from typing import Dict, Any, Optional
import logging
from fastapi import HTTPException
from datetime import datetime

from application.services.document_processing_service import DocumentProcessingService
from application.services.document_chunking_service import DocumentChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.document_storage_service import DocumentStorageService
from shared.interfaces.repositories.document_repository import DocumentRepository
from domain.entities.document import Document

logger = logging.getLogger(__name__)

class DocumentProcessingPipelineService:
    """Service for orchestrating the complete document processing pipeline."""

    def __init__(
        self,
        document_processing_service: DocumentProcessingService,
        document_chunking_service: DocumentChunkingService,
        kb_sync_service: KBSyncService,
        document_repository: DocumentRepository,
        kb_config: Dict[str, str],
        document_storage_service: DocumentStorageService | None = None
    ):
        """
        Initialize pipeline service.

        Args:
            document_processing_service: Service for text extraction
            document_chunking_service: Service for text chunking
            kb_sync_service: Service for KB syncing
            document_repository: Repository for document operations
            kb_config: Configuration mapping domains to KB IDs
        """
        self.document_processing = document_processing_service
        self.document_chunking = document_chunking_service
        self.kb_sync = kb_sync_service
        self.document_repository = document_repository
        self.kb_config = kb_config
        # Document storage service (can be injected for testing)
        self.document_storage = document_storage_service or DocumentStorageService()

    async def process_document(
        self,
        document_id: str,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline.

        Args:
            document_id: ID of document to process
            force_reprocess: Whether to reprocess even if already processed

        Returns:
            Dictionary with processing results
        """
        try:
            # Get document
            document = await self.document_repository.find_by_id(document_id)
            if not document:
                raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

            # Check if already processed and not forcing reprocess
            if document.processing_status == "completed" and not force_reprocess:
                return {
                    "status": "already_processed",
                    "document_id": document_id,
                    "message": "Document already processed"
                }

            # Step 1: Extract text
            logger.info(f"Extracting text from document {document_id}")
            text = await self._extract_text(document)

            # Step 2: Create chunks
            logger.info(f"Creating chunks for document {document_id}")
            chunks = await self._create_chunks(document, text)

            # Step 3: Get KB ID for domain
            kb_id = self.kb_config.get(document.domain.lower())
            if not kb_id:
                raise ValueError(f"No Knowledge Base configured for domain: {document.domain}")

            # Step 4: Sync with KB
            logger.info(f"Syncing document {document_id} to KB {kb_id}")
            sync_result = await self.kb_sync.add_document_to_kb(document, chunks, kb_id)

            if not sync_result["success"]:
                raise Exception(f"KB sync failed: {sync_result.get('error')}")

            return {
                "status": "success",
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "kb_id": kb_id,
                **sync_result
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            # Update document status
            if document:
                document.mark_as_failed(str(e))
                await self.document_repository.update(document)
            raise

    async def _extract_text(self, document: Document) -> str:
        """Extract text from document file."""
        try:
            # Get file content from S3 via the document storage service
            file_content = await self.document_storage.get_file_content(document)
            
            # Extract text
            text = await self.document_processing.extract_text(
                file_content,
                document.filename,
                document.content_type
            )

            if not self.document_processing.validate_extracted_text(text):
                raise ValueError("No valid text content could be extracted")

            return text

        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise

    async def _create_chunks(self, document: Document, text: str) -> list:
        """Create chunks from document text."""
        try:
            # Create chunks
            chunks = await self.document_chunking.chunk_text(
                text=text,
                document_id=str(document.id),
                filename=document.filename,
                domain=document.domain
            )

            if not chunks:
                raise ValueError("Chunking produced no valid chunks")

            # Log chunking statistics
            stats = self.document_chunking.get_chunking_statistics(chunks)
            logger.info(f"Chunking stats for {document.id}: {stats}")

            return chunks

        except Exception as e:
            logger.error(f"Chunking failed: {str(e)}")
            raise

    async def bulk_process_documents(
        self,
        document_ids: list[str],
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple documents in parallel.

        Args:
            document_ids: List of document IDs to process
            force_reprocess: Whether to reprocess already processed documents

        Returns:
            Dictionary with bulk processing results
        """
        results = []
        for doc_id in document_ids:
            try:
                result = await self.process_document(doc_id, force_reprocess)
                results.append({
                    "document_id": doc_id,
                    "status": "success",
                    **result
                })
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "total": len(document_ids),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }