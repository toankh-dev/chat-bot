"""
User SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class UserChatbot(Base):
    """
    Direct assignment of chatbots to individual users.
    """
    __tablename__ = "user_chatbots"
    __table_args__ = {'extend_existing': True}

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"), primary_key=True)
    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Admin who assigned this chatbot to the user"
    )
    assigned_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="active", comment="active, revoked")

    # Relationships
    user = relationship("User", back_populates="user_chatbots", foreign_keys=[user_id])
    chatbot = relationship("Chatbot", back_populates="user_chatbots")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


