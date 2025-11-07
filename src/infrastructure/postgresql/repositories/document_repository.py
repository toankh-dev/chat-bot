from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from shared.interfaces.repositories.document_repository import DocumentRepository
from domain.entities.document import Document
from domain.value_objects.uuid_vo import UUID
from infrastructure.postgresql.models.document_model import DocumentModel
from datetime import datetime

class DocumentRepositoryImpl(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, document: Document) -> Document:
        """Save or update a document."""
        doc_model = DocumentModel(
            id=str(document.id.value),
            filename=document.filename,
            file_size=document.file_size,
            content_type=document.content_type,
            s3_key=document.s3_key,
            domain=document.domain,
            user_id=document.user_id,
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            error_message=document.error_message,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at
        )
        
        # Check if document exists
        existing = await self._session.get(DocumentModel, str(document.id.value))
        if existing:
            # Update existing
            for key, value in doc_model.__dict__.items():
                if not key.startswith('_') and value is not None:
                    setattr(existing, key, value)
            await self._session.commit()
            return self._to_domain(existing)
        else:
            # Create new
            self._session.add(doc_model)
            await self._session.commit()
            return self._to_domain(doc_model)
    
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find document by ID."""
        result = await self._session.get(DocumentModel, document_id)
        return self._to_domain(result) if result else None
    
    async def find_by_user_id(
        self, 
        user_id: str, 
        domain: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Find documents by user ID with optional domain filter."""
        query = select(DocumentModel).where(DocumentModel.user_id == user_id)
        
        if domain:
            query = query.where(DocumentModel.domain == domain)
        
        query = query.offset(skip).limit(limit).order_by(DocumentModel.uploaded_at.desc())
        
        result = await self._session.execute(query)
        doc_models = result.scalars().all()
        
        return [self._to_domain(doc_model) for doc_model in doc_models]
    
    async def delete_by_id(self, document_id: str) -> bool:
        """Delete document by ID."""
        result = await self._session.execute(
            delete(DocumentModel).where(DocumentModel.id == document_id)
        )
        await self._session.commit()
        return result.rowcount > 0
    
    async def update_status(
        self, 
        document_id: str, 
        upload_status: Optional[str] = None,
        processing_status: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update document status."""
        doc_model = await self._session.get(DocumentModel, document_id)
        if not doc_model:
            return False
        
        if upload_status:
            doc_model.upload_status = upload_status
        if processing_status:
            doc_model.processing_status = processing_status
            if processing_status == "completed":
                doc_model.processed_at = datetime.utcnow()
        if error_message is not None:
            doc_model.error_message = error_message
        
        await self._session.commit()
        return True
    
    def _to_domain(self, doc_model: DocumentModel) -> Document:
        """Convert database model to domain entity."""
        return Document(
            id=UUID(doc_model.id),
            filename=doc_model.filename,
            file_size=doc_model.file_size,
            content_type=doc_model.content_type,
            s3_key=doc_model.s3_key,
            domain=doc_model.domain,
            user_id=doc_model.user_id,
            upload_status=doc_model.upload_status,
            processing_status=doc_model.processing_status,
            error_message=doc_model.error_message,
            uploaded_at=doc_model.uploaded_at,
            processed_at=doc_model.processed_at
        )