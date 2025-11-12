"""
KnowledgeBase SQLAlchemy model.

Represents knowledge_bases table in PostgreSQL.
"""

from sqlalchemy import Boolean, Column, Integer, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class KnowledgeBaseModel(Base):
    """
    Knowledge Base SQLAlchemy model.

    Maps to knowledge_bases table.
    """

    __tablename__ = "knowledge_bases"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    vector_store_type = Column(String(50), nullable=False, server_default="chromadb")
    vector_store_collection = Column(String(255), nullable=True)
    vector_store_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    chatbot = relationship("ChatbotModel", back_populates="knowledge_bases")
    sources = relationship("KnowledgeBaseSourceModel", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<KnowledgeBaseModel(id={self.id}, chatbot_id={self.chatbot_id}, name='{self.name}')>"
