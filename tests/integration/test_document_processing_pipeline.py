"""
End-to-end test for document processing pipeline.
"""

import os
import pytest
import asyncio
from typing import Dict, Any
from src.domain.entities.document import DocumentEntity
from src.application.services.document_processing_pipeline_service import DocumentProcessingPipelineService
from src.application.services.document_processing_service import DocumentProcessingService
from src.application.services.document_chunking_service import DocumentChunkingService
from src.application.services.kb_sync_service import KBSyncService
from src.infrastructure.postgresql.repositories.document_repository import DocumentRepositoryImpl
from src.infrastructure.ai_services.embeddings.factory import EmbeddingFactory
from src.infrastructure.ai_services.llm.factory import LLMFactory
from src.infrastructure.vector_store.factory import VectorStoreFactory
from src.infrastructure.s3.s3_file_storage_service import S3FileStorageService
from tests.mocks.s3_service_mock import S3FileStorageServiceMock

# Test configuration
TEST_CONFIG = {
    "general": "kb_general_test",
    "healthcare": "kb_healthcare_test",
    "finance": "kb_finance_test"
}

@pytest.fixture
async def setup_pipeline(db_session, s3_service):
    """Setup test pipeline with all required services."""
    # Initialize services
    document_processing = DocumentProcessingService()
    document_chunking = DocumentChunkingService(
        chunk_size=1000,
        chunk_overlap=200,
        max_chunks=500
    )
    
    # Initialize repositories and services
    document_repository = DocumentRepositoryImpl(session=db_session)
    
    # Create services using factories
    llm_service = LLMFactory.create()
    embedding_service = EmbeddingFactory.create()
    vector_store = VectorStoreFactory.create(
        config={"persist_directory": ".chromadb_test"}
    )
    
    kb_sync = KBSyncService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        document_repository=document_repository
    )
    
    pipeline = DocumentProcessingPipelineService(
        document_processing_service=document_processing,
        document_chunking_service=document_chunking,
        kb_sync_service=kb_sync,
        document_repository=document_repository,
        kb_config=TEST_CONFIG
    )
    
    return pipeline, document_repository, s3_service

async def create_test_document(repository: DocumentRepositoryImpl, s3_service: S3FileStorageServiceMock) -> DocumentEntity:
    """Create a test document in the database."""
    # Create test data directory if it doesn't exist
    test_data_dir = os.path.join('tests', 'data')
    os.makedirs(test_data_dir, exist_ok=True)

    # Create test document file if it doesn't exist
    test_file_path = os.path.join('tests', 'data', 'test_document.txt')
    # Create test document file if it doesn't exist
    test_content = "This is a test document for integration testing.\nIt contains multiple lines of text.\nThe content is used to test the document processing pipeline.\n"
    with open(test_file_path, 'wb') as f:
        f.write(test_content.encode('utf-8'))

    with open(test_file_path, 'rb') as f:
        content = f.read()
    
    # Create document entity
    document = DocumentEntity(
        id=None,  # Will be set by repository
        filename="test_document.txt",
        file_size=len(content),
        content_type="text/plain",
        s3_key="test/documents/test_document.txt",
        domain="general",
        user_id="test_user",
        upload_status="uploaded"
    )
    
    # Save to database
    document = await repository.create(document)
    
    # Upload to mock S3
    await s3_service.put_file(document.s3_key, content)
    
    return document

@pytest.mark.asyncio
async def test_document_processing_pipeline(setup_pipeline):
    """Test complete document processing pipeline."""
    pipeline, repository, s3_service = setup_pipeline
    document = None

    try:
        # Step 1: Create test document
        document = await create_test_document(repository, s3_service)
        assert document.id is not None, "Document should have ID after creation"

        # Step 2: Process document
        result = await pipeline.process_document(str(document.id))
        assert result["status"] == "success", f"Processing failed: {result.get('error', 'Unknown error')}"

        # Verify chunks were created
        assert result["chunks_processed"] > 0, "No chunks were created"
        assert result["kb_id"] == TEST_CONFIG["general"], "Wrong KB ID used"

        # Step 3: Verify document status
        processed_doc = await repository.find_by_id(document.id)
        assert processed_doc.processing_status == "completed", "Document should be marked as completed"
        assert processed_doc.knowledge_base_id == TEST_CONFIG["general"], "Document should have KB ID set"

        print("\nProcessing Results:")
        print(f"Document ID: {document.id}")
        print(f"Chunks Processed: {result['chunks_processed']}")
        print(f"Knowledge Base: {result['kb_id']}")
        print(f"Processing Status: {processed_doc.processing_status}")

    finally:
        # Cleanup
        if document:
            await repository.delete(document.id)
            print(f"\nCleanup: Deleted test document {document.id}")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_document_processing_pipeline())