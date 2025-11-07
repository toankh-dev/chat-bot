"""
Document entity mapper.
"""

from typing import Optional
from domain.entities.document import Document as DocumentEntity
from infrastructure.postgresql.models.document_model import DocumentModel


class DocumentMapper:
    """Maps between Document entity and DocumentModel."""
    
    @staticmethod
    def to_entity(model: DocumentModel) -> DocumentEntity:
        """Convert DocumentModel to Document entity."""
        return DocumentEntity(
            id=model.id,
            filename=model.filename,
            file_size=model.file_size,
            content_type=model.content_type,
            s3_key=model.s3_key,
            domain=model.domain,
            user_id=model.user_id,
            upload_status=model.upload_status,
            processing_status=model.processing_status,
            error_message=model.error_message,
            uploaded_at=model.uploaded_at,
            processed_at=model.processed_at
        )
    
    @staticmethod
    def to_model(entity: DocumentEntity) -> DocumentModel:
        """Convert Document entity to DocumentModel."""
        return DocumentModel(
            id=entity.id,
            filename=entity.filename,
            file_size=entity.file_size,
            content_type=entity.content_type,
            s3_key=entity.s3_key,
            domain=entity.domain,
            user_id=entity.user_id,
            upload_status=entity.upload_status,
            processing_status=entity.processing_status,
            error_message=entity.error_message,
            uploaded_at=entity.uploaded_at,
            processed_at=entity.processed_at
        )