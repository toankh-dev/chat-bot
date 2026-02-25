"""
ChatbotTool SQLAlchemy ORM model.

Stores tool configurations for chatbots.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class ChatbotToolModel(Base):
    """
    Chatbot tool configuration model.

    Allows enabling/configuring tools available to chatbots.
    """
    __tablename__ = "chatbot_tools"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chatbot_id = Column(
        Integer,
        ForeignKey("chatbots.id", ondelete="CASCADE"),
        nullable=False
    )
    tool_name = Column(String(100), nullable=False)
    description = Column(Text)
    tool_config = Column(Text, comment="JSON tool configuration")
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    chatbot = relationship("ChatbotModel", back_populates="chatbot_tools")