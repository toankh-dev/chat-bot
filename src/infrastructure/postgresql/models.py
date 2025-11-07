"""
SQLAlchemy ORM models based on init.sql schema.

This module defines all database tables matching the existing schema.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Numeric,
    ForeignKey, Index, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    User account model.

    Represents system users with authentication and authorization.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_admin = Column(Boolean, default=False, comment="Admin can create users, chatbots, and groups")
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False, comment="Encrypted password (bcrypt)")
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="active", comment="active, disabled, suspended")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    created_chatbots = relationship("Chatbot", back_populates="creator", foreign_keys="Chatbot.created_by")
    user_groups = relationship("UserGroup", back_populates="user", foreign_keys="UserGroup.user_id")
    user_chatbots = relationship("UserChatbot", back_populates="user", foreign_keys="UserChatbot.user_id")
    conversations = relationship("Conversation", back_populates="user")
    message_feedbacks = relationship("MessageFeedback", back_populates="user")


class Group(Base):
    """
    User group model for organizing users.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user_groups = relationship("UserGroup", back_populates="group")
    group_chatbots = relationship("GroupChatbot", back_populates="group")


class UserGroup(Base):
    """
    Many-to-many relationship between users and groups.
    """
    __tablename__ = "user_groups"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    added_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="Admin who added this user to the group"
    )
    joined_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_groups", foreign_keys=[user_id])
    group = relationship("Group", back_populates="user_groups")
    added_by_user = relationship("User", foreign_keys=[added_by])


class Chatbot(Base):
    """
    Chatbot configuration model.

    Stores AI model settings and behavior configuration.
    """
    __tablename__ = "chatbots"

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
    creator = relationship("User", back_populates="created_chatbots", foreign_keys=[created_by])
    group_chatbots = relationship("GroupChatbot", back_populates="chatbot", cascade="all, delete-orphan")
    user_chatbots = relationship("UserChatbot", back_populates="chatbot", cascade="all, delete-orphan")
    chatbot_tools = relationship("ChatbotTool", back_populates="chatbot")
    conversations = relationship("Conversation", back_populates="chatbot")


class GroupChatbot(Base):
    """
    Assignment of chatbots to groups.
    """
    __tablename__ = "group_chatbots"

    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"), primary_key=True)
    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Admin who assigned this chatbot to the group"
    )
    assigned_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="active", comment="active, revoked")

    # Relationships
    group = relationship("Group", back_populates="group_chatbots")
    chatbot = relationship("Chatbot", back_populates="group_chatbots")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class UserChatbot(Base):
    """
    Direct assignment of chatbots to individual users.
    """
    __tablename__ = "user_chatbots"

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


class Tool(Base):
    """
    Available tools that chatbots can use.
    """
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment="Hard-coded tool identifier")
    description = Column(Text, comment="Description of what this tool does")
    status = Column(String(20), default="active", comment="active, disabled")

    # Relationships
    chatbot_tools = relationship("ChatbotTool", back_populates="tool")


class ChatbotTool(Base):
    """
    Tools enabled for specific chatbots.
    """
    __tablename__ = "chatbot_tools"

    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="CASCADE"), primary_key=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime, default=func.now())

    # Relationships
    chatbot = relationship("Chatbot", back_populates="chatbot_tools")
    tool = relationship("Tool", back_populates="chatbot_tools")


class Conversation(Base):
    """
    Chat conversation session.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chatbot_id = Column(Integer, ForeignKey("chatbots.id", ondelete="SET NULL"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    title = Column(String(255), comment="Conversation title, auto-generated or user-defined")
    status = Column(String(20), default="active", comment="active, archived, deleted")
    is_active = Column(
        Boolean,
        default=True,
        comment="Whether this conversation is currently active for the user"
    )
    started_at = Column(DateTime, default=func.now())
    last_message_at = Column(DateTime, comment="Updated with each new message")
    last_accessed_at = Column(
        DateTime,
        default=func.now(),
        comment="Updated when user accesses the conversation"
    )
    message_count = Column(Integer, default=0, comment="Total messages in conversation")

    # Relationships
    chatbot = relationship("Chatbot", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """
    Individual message in a conversation.
    """
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role = Column(String(20), nullable=False, comment="user, assistant, system, tool")
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, comment="Additional data: tokens, tool calls, timing")
    created_at = Column(DateTime, default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")


class MessageFeedback(Base):
    """
    User feedback on AI responses.
    """
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="The assistant message being rated"
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_positive = Column(Boolean, nullable=False, comment="true = good, false = not good")
    is_reviewed = Column(
        Boolean,
        default=False,
        comment="Whether admin has reviewed this feedback"
    )
    note = Column(Text, comment="Optional comment about the feedback")
    created_at = Column(DateTime, default=func.now())

    # Relationships
    message = relationship("Message", back_populates="feedbacks")
    user = relationship("User", back_populates="message_feedbacks")
