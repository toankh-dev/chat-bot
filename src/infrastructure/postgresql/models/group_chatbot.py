"""
User SQLAlchemy ORM model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .user_model import UserModel
from sqlalchemy.sql import func

from infrastructure.postgresql.connection.base import Base


class GroupChatbotModel(Base):
    """
    Assignment of chatbots to groups.
    """

    __tablename__ = "group_chatbots"
    __table_args__ = {'extend_existing': True}

    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"), primary_key=True)
    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Admin who assigned this chatbot to the group",
    )
    assigned_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="active", comment="active, revoked")

    # Relationships
    group = relationship("Group", back_populates="group_chatbots")
    chatbot = relationship("ChatbotModel", back_populates="group_chatbots")
    assigned_by_user = relationship(UserModel, foreign_keys=[assigned_by])
