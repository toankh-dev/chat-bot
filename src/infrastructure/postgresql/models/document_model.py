from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from infrastructure.postgresql.connection.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    upload_status = Column(String, nullable=False)  # uploading, uploaded, processing, processed, failed
    processing_status = Column(String)  # pending, in_progress, completed, failed
    error_message = Column(Text)
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)