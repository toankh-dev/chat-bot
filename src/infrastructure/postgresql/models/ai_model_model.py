"""
AI Model SQLAlchemy model.

ORM model for ai_models table.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from infrastructure.postgresql.connection.base import Base


class AiModelModel(Base):
    """
    AI Model ORM model.
    
    Represents ai_models table in the database.
    """
    
    __tablename__ = "ai_models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True, comment="Model name (e.g., gpt-4o, claude-3-5-sonnet)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    chatbots = relationship("ChatbotModel", back_populates="ai_model")
    
    def __repr__(self):
        return f"<AiModel(id={self.id}, name='{self.name}')>"

