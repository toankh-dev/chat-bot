from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from infrastructure.postgresql.connection.base import Base


class ConversationModel(Base):
    """Chat conversation session."""
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="SET NULL"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    title = Column(String(255))
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=func.now())
    last_message_at = Column(DateTime)
    last_accessed_at = Column(DateTime, default=func.now())
    message_count = Column(Integer, default=0)

    # Relationships
    chatbot = relationship("ChatbotModel", back_populates="conversations")
    user = relationship("UserModel", back_populates="conversations")
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")

class MessageModel(Base):
    """Chat message within a conversation."""
    __tablename__ = "messages"
    __table_args__ = (
        Index('idx_messages_conversation_id', 'conversation_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    msg_metadata = Column('metadata', JSON)  # Map to 'metadata' column but use 'msg_metadata' attribute
    created_at = Column(DateTime, default=func.now())

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")

