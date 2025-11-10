from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class IFileStorageService(ABC):
    @abstractmethod
    async def get_file(self, file_key: str) -> bytes:
        """Get file content from S3."""
        pass

    @abstractmethod
    async def upload_file(self, file_content: BinaryIO, s3_key: str, content_type: str) -> str:
        """Upload file to S3 and return URL."""
        pass
    
    @abstractmethod
    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3."""
        pass
    
    @abstractmethod
    async def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for file access."""
        pass