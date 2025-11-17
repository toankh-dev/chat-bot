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

class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""
    message: str = Field(..., description="Success message")

    class Config:
        from_attributes = True