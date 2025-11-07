from shared.interfaces.services.upload.document_upload_service import IDocumentUploadService
from shared.interfaces.repositories.document_repository import DocumentRepository
from typing import List
from domain.entities.document import Document

class UploadDocumentUseCase:
    def __init__(self, document_upload_service: IDocumentUploadService):
        self.document_upload_service = document_upload_service
    
    async def execute(self, file_content, filename: str, content_type: str, 
                     user_id: str, domain: str) -> Document:
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
    
    async def execute(self, user_id: str, domain: str = None, skip: int = 0, limit: int = 100) -> List[Document]:
        if domain:
            return await self.document_repository.find_by_user_and_domain(user_id, domain, skip, limit)
        # If no domain specified, would need a find_by_user method
        return []