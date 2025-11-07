from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from infrastructure.postgresql.connection.base import Base


class Chatbot(Base):
    """Chatbot configuration model."""
    __tablename__ = "chatbots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(Numeric(3, 2), default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Numeric(3, 2), default=1.0)
    system_prompt = Column(Text)
    welcome_message = Column(Text)
    fallback_message = Column(Text)
    max_conversation_length = Column(Integer, default=50)
    enable_function_calling = Column(Boolean, default=True)
    api_key_encrypted = Column(Text, nullable=False)
    api_base_url = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())