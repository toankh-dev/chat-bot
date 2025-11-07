from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from shared.interfaces.repositories.document_repository import DocumentRepository
from domain.entities.document import Document
from domain.value_objects.uuid_vo import UUID
from typing import BinaryIO
import os

class DocumentUploadService(IDocumentUploadService):
    def __init__(self, file_storage_service: IFileStorageService, document_repository: DocumentRepository):
        self.file_storage_service = file_storage_service
        self.document_repository = document_repository
        self.allowed_extensions = {".pdf", ".docx", ".txt", ".md"}
        self.allowed_content_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown"
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    async def upload_document(self, file_content: BinaryIO, filename: str, content_type: str, 
                            user_id: str, domain: str) -> Document:
        file_size = self._get_file_size(file_content)
        
        if not self.validate_file(filename, content_type, file_size):
            raise ValueError("Invalid file format or size")
        
        document_id = UUID.generate()
        s3_key = f"raw-documents/{domain}/{user_id}/{document_id}/{filename}"
        
        document = Document(
            id=document_id,
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            domain=domain,
            s3_key=s3_key,
            upload_status="uploading"
        )
        
        await self.file_storage_service.upload_file(file_content, s3_key, content_type)
        document.mark_as_uploaded()
        
        return await self.document_repository.create(document)
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        document = await self.document_repository.find_by_id(document_id)
        
        if not document or document.user_id != user_id:
            return False
        
        file_deleted = await self.file_storage_service.delete_file(document.s3_key)
        record_deleted = await self.document_repository.delete(document_id)
        
        return file_deleted and record_deleted
    
    def validate_file(self, filename: str, content_type: str, file_size: int) -> bool:
        if file_size > self.max_file_size:
            return False
        
        if content_type not in self.allowed_content_types:
            return False
        
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            return False
        
        return True
    
    def _get_file_size(self, file_content: BinaryIO) -> int:
        current_position = file_content.tell()
        file_content.seek(0, 2)  # Seek to end
        size = file_content.tell()
        file_content.seek(current_position)  # Reset position
        return size