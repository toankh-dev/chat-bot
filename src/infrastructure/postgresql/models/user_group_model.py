"""
UserGroup SQLAlchemy model.

ORM model for user_groups junction table.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from .user_model import UserModel
from infrastructure.postgresql.connection.base import Base


class UserGroup(Base):
    """
    UserGroup ORM model.

    Represents user_groups junction table in the database.
    Junction table with composite primary key (user_id, group_id).
    """

    __tablename__ = "user_groups"
    __table_args__ = {'extend_existing': True}

    # Composite primary key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    added_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    joined_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=True)

    # Relationships
    user = relationship(UserModel, foreign_keys=[user_id])
    group = relationship("Group", back_populates="user_groups")
    added_by_user = relationship(UserModel, foreign_keys=[added_by])

    def __repr__(self):
        return f"<UserGroup(user_id={self.user_id}, group_id={self.group_id})>"