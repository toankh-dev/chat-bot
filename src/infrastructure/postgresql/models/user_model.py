"""
User SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from infrastructure.postgresql.connection.base import Base


class UserModel(Base):
    """User account model."""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_admin = Column(Boolean, default=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship: all chatbots created by this user
    created_chatbots = relationship(
        "ChatbotModel",
        back_populates="creator",
        foreign_keys="ChatbotModel.created_by"
    )
    
    # User's chat conversations
    conversations = relationship(
        "ConversationModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # User's direct chatbot assignments
    user_chatbots = relationship(
        "UserChatbotModel",
        back_populates="user",
        foreign_keys="UserChatbotModel.user_id",
        cascade="all, delete-orphan"
    )