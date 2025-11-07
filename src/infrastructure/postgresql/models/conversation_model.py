from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from infrastructure.postgresql.connection.base import Base


class Conversation(Base):
    """Chat conversation session."""
    __tablename__ = "conversations"

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


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(Text)  # JSON as text for compatibility
    created_at = Column(DateTime, default=func.now())