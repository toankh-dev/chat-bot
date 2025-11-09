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
    knowledge_base_id: Optional[str] = Field(None, description="Knowledge Base ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")


class DocumentProcessingResponse(BaseModel):
    success: bool = Field(..., description="Whether processing succeeded")
    document_id: str = Field(..., description="Document ID")
    kb_id: Optional[str] = Field(None, description="Knowledge Base ID")
    total_chunks: Optional[int] = Field(None, description="Total chunks created")
    vectors_added: Optional[int] = Field(None, description="Number of vectors added to KB")
    text_statistics: Optional[dict] = Field(None, description="Text extraction statistics")
    chunk_statistics: Optional[dict] = Field(None, description="Chunking statistics")
    error: Optional[str] = Field(None, description="Error message if failed")