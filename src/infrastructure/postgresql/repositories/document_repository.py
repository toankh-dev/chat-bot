from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy import select, delete
from shared.interfaces.repositories.document_repository import DocumentRepository
from domain.entities.document import DocumentEntity
from domain.value_objects.uuid_vo import UUID
from infrastructure.postgresql.models.document_model import DocumentModel
from datetime import datetime, UTC

class DocumentRepositoryImpl(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create new document."""
        # Generate ID if not provided
        document_id = document.id if document.id else UUID.generate()

        # Convert timezone-aware datetime to naive UTC datetime for PostgreSQL
        uploaded_at = document.uploaded_at.replace(tzinfo=None) if document.uploaded_at and document.uploaded_at.tzinfo else document.uploaded_at
        processed_at = document.processed_at.replace(tzinfo=None) if document.processed_at and document.processed_at.tzinfo else document.processed_at

        doc_model = DocumentModel(
            id=str(uuid.UUID(str(document_id.value))),
            filename=document.filename,
            file_size=document.file_size,
            content_type=document.content_type,
            s3_key=document.s3_key,
            domain=document.domain,
            user_id=document.user_id,
            upload_status=document.upload_status,
            processing_status=document.processing_status,
            knowledge_base_id=document.knowledge_base_id,
            error_message=document.error_message,
            uploaded_at=uploaded_at,
            processed_at=processed_at
        )

        # Create new
        self._session.add(doc_model)
        await self._session.commit()
        return self._to_domain(doc_model)
    
    async def find_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """Find document by ID."""
        # Convert string to UUID for lookup
        try:
            db_id = str(uuid.UUID(str(document_id)))
        except ValueError:
            return None
        
        result = await self._session.get(DocumentModel, db_id)
        return self._to_domain(result) if result else None
    
    async def find_by_user_and_domain(
        self, 
        user_id: str, 
        domain: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentEntity]:
        """Find documents by user ID and domain."""
        query = select(DocumentModel).where(
            (DocumentModel.user_id == user_id) & 
            (DocumentModel.domain == domain)
        )
        
        query = query.offset(skip).limit(limit).order_by(DocumentModel.uploaded_at.desc())
        
        result = await self._session.execute(query)
        doc_models = result.scalars().all()
        
        return [self._to_domain(doc_model) for doc_model in doc_models]
    
    async def delete(self, document_id: str) -> bool:
        """Delete document by ID."""
        try:
            db_id = str(uuid.UUID(str(document_id)))
        except ValueError:
            return False

        result = await self._session.execute(
            delete(DocumentModel).where(DocumentModel.id == db_id)
        )
        await self._session.commit()
        return result.rowcount > 0
    
    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update existing document."""
        doc_model = await self._session.get(DocumentModel, str(uuid.UUID(str(document.id.value))))
        if not doc_model:
            raise ValueError(f"Document not found: {document.id}")

        # Convert timezone-aware datetime to naive UTC datetime for PostgreSQL
        uploaded_at = document.uploaded_at.replace(tzinfo=None) if document.uploaded_at and document.uploaded_at.tzinfo else document.uploaded_at
        processed_at = document.processed_at.replace(tzinfo=None) if document.processed_at and document.processed_at.tzinfo else document.processed_at

        # Update all fields
        doc_model.filename = document.filename
        doc_model.file_size = document.file_size
        doc_model.content_type = document.content_type
        doc_model.s3_key = document.s3_key
        doc_model.domain = document.domain
        doc_model.user_id = document.user_id
        doc_model.upload_status = document.upload_status
        doc_model.processing_status = document.processing_status
        doc_model.knowledge_base_id = document.knowledge_base_id
        doc_model.error_message = document.error_message
        doc_model.uploaded_at = uploaded_at
        doc_model.processed_at = processed_at

        await self._session.commit()
        await self._session.refresh(doc_model)
        return self._to_domain(doc_model)

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
    
    async def find_by_knowledge_base(
        self,
        knowledge_base_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentEntity]:
        """Find documents by Knowledge Base ID."""
        query = select(DocumentModel).where(
            DocumentModel.knowledge_base_id == knowledge_base_id
        ).offset(skip).limit(limit).order_by(DocumentModel.processed_at.desc())

        result = await self._session.execute(query)
        doc_models = result.scalars().all()

        return [self._to_domain(doc_model) for doc_model in doc_models]

    def _to_domain(self, doc_model: DocumentModel) -> DocumentEntity:
        """Convert database model to domain entity."""
        return DocumentEntity(
            id=UUID(doc_model.id),
            filename=doc_model.filename,
            file_size=doc_model.file_size,
            content_type=doc_model.content_type,
            s3_key=doc_model.s3_key,
            domain=doc_model.domain,
            user_id=doc_model.user_id,
            upload_status=doc_model.upload_status,
            processing_status=doc_model.processing_status,
            knowledge_base_id=doc_model.knowledge_base_id,
            error_message=doc_model.error_message,
            uploaded_at=doc_model.uploaded_at,
            processed_at=doc_model.processed_at
        )