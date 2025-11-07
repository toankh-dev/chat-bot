from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.document import Document

class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create new document record."""
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find document by ID."""
        pass
    
    @abstractmethod
    async def find_by_user_and_domain(self, user_id: str, domain: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """Find documents by user and domain."""
        pass
    
    @abstractmethod
    async def update_status(self, document_id: str, status: str, processing_status: Optional[str] = None, error_message: Optional[str] = None) -> bool:
        """Update document processing status."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete document record."""
        pass