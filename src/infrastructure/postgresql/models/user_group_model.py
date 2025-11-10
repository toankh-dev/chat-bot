"""
UserGroup SQLAlchemy model.

ORM model for user_groups junction table.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .user_model import UserModel
from infrastructure.postgresql.connection.base import Base


class UserGroup(Base):
    """
    UserGroup ORM model.
    
    Represents user_groups junction table in the database.
    """
    
    __tablename__ = "user_groups"
    __table_args__ = {'extend_existing': True}

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True, nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship(UserModel, foreign_keys=[user_id])
    group = relationship("Group", back_populates="user_groups")
    added_by_user = relationship(UserModel, foreign_keys=[added_by])
    
    def __repr__(self):
        return f"<UserGroup(user_id={self.user_id}, group_id={self.group_id})>"