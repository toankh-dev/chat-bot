from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class ChatbotModel(Base):
    """
    Chatbot configuration model.

    Stores AI model settings and behavior configuration.
    """
    __tablename__ = "chatbots"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    provider = Column(String(50), nullable=False, comment="openai, anthropic, google")
    model = Column(String(100), nullable=False, comment="gpt-4o, claude-3-5-sonnet, gemini-pro")
    temperature = Column(Numeric(3, 2), default=0.7, comment="0.0-2.0, controls randomness")
    max_tokens = Column(Integer, default=2048, comment="Maximum response length")
    top_p = Column(Numeric(3, 2), default=1.0, comment="0.0-1.0, nucleus sampling")
    system_prompt = Column(Text, comment="Instructions defining bot personality and behavior")
    welcome_message = Column(Text, comment="First message sent to users")
    fallback_message = Column(Text, comment="Response when API fails")
    max_conversation_length = Column(
        Integer,
        default=50,
        comment="Messages to remember in context"
    )
    enable_function_calling = Column(
        Boolean,
        default=True,
        comment="Allow AI to use available tools"
    )
    api_key_encrypted = Column(Text, nullable=False, comment="Encrypted API credentials")
    api_base_url = Column(
        String(500),
        comment="Custom API endpoint for Azure/custom deployments"
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="Admin who created this chatbot"
    )
    status = Column(String(20), default="active", comment="active, disabled, archived")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("UserModel", back_populates="created_chatbots", foreign_keys=[created_by])
    group_chatbots = relationship("GroupChatbotModel", back_populates="chatbot", cascade="all, delete-orphan")
    user_chatbots = relationship("UserChatbotModel", back_populates="chatbot", cascade="all, delete-orphan")
    chatbot_tools = relationship("ChatbotToolModel", back_populates="chatbot")
    conversations = relationship("ConversationModel", back_populates="chatbot")

