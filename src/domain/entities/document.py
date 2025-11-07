from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.value_objects.uuid_vo import UUID

@dataclass
class Document:
    id: UUID
    user_id: str
    filename: str
    file_size: int
    content_type: str
    domain: str
    s3_key: str
    upload_status: str  # uploading, uploaded, processing, processed, failed
    processing_status: Optional[str] = None  # pending, syncing, completed, error
    knowledge_base_id: Optional[str] = None
    error_message: Optional[str] = None
    uploaded_at: datetime = datetime.utcnow()
    processed_at: Optional[datetime] = None
    
    def mark_as_uploaded(self):
        self.upload_status = "uploaded"
    
    def mark_as_processing(self, kb_id: str):
        self.upload_status = "processing"
        self.processing_status = "pending"
        self.knowledge_base_id = kb_id
    
    def mark_as_processed(self):
        self.upload_status = "processed"
        self.processing_status = "completed"
        self.processed_at = datetime.utcnow()
    
    def mark_as_failed(self, error: str):
        self.upload_status = "failed"
        self.processing_status = "error"
        self.error_message = error