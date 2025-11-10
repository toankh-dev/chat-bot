"""
Group SQLAlchemy model.

ORM model for groups table.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from infrastructure.postgresql.connection.base import Base


class Group(Base):
    """
    Group ORM model.
    
    Represents groups table in the database.
    """
    
    __tablename__ = "groups"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_groups = relationship("UserGroup", back_populates="group", cascade="all, delete-orphan")
    group_chatbots = relationship("GroupChatbotModel", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name='{self.name}')>"