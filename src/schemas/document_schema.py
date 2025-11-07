from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    domain: str = Field(..., description="Document domain")
    upload_status: str = Field(..., description="Upload status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

class DocumentListResponse(BaseModel):
    documents: List[DocumentUploadResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total document count")

class DocumentStatusResponse(BaseModel):
    id: str = Field(..., description="Document ID")
    upload_status: str = Field(..., description="Upload status")
    processing_status: Optional[str] = Field(None, description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")