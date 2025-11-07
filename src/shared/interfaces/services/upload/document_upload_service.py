from abc import ABC, abstractmethod
from typing import BinaryIO
from domain.entities.document import Document

class IDocumentUploadService(ABC):
    @abstractmethod
    async def upload_document(self, file_content: BinaryIO, filename: str, content_type: str, 
                            user_id: str, domain: str) -> Document:
        """Upload document and create record."""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document and file."""
        pass
    
    @abstractmethod
    def validate_file(self, filename: str, content_type: str, file_size: int) -> bool:
        """Validate file before upload."""
        pass