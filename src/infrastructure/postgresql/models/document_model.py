from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from infrastructure.postgresql.connection.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    upload_status = Column(String, nullable=False)  # uploading, uploaded, processing, processed, failed
    processing_status = Column(String)  # pending, syncing, completed, error
    knowledge_base_id = Column(String)  # KB ID where document is indexed
    error_message = Column(Text)
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)