from typing import TYPE_CHECKING, Optional
from infrastructure.s3.s3_file_storage_service import S3FileStorageService

if TYPE_CHECKING:
    from domain.entities.document import DocumentEntity  # type: ignore


class DocumentStorageService:
    """Service that provides access to document file contents stored in S3.

    This service centralizes interactions with the S3 storage implementation so
    domain entities don't depend on infrastructure modules directly.
    """

    def __init__(self, s3_service: Optional[S3FileStorageService] = None) -> None:
        self._s3 = s3_service or S3FileStorageService()

    async def get_file_content(self, document: "DocumentEntity") -> bytes:
        """Return raw file bytes for the given document entity."""
        return await self._s3.get_file(document.s3_key)
