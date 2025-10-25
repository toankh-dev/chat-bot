"""
Conversation Store using PostgreSQL for conversation history
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

Base = declarative_base()


class Conversation(Base):
    """Conversation model"""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationStore:
    """
    Store for managing conversation history in PostgreSQL
    """

    def __init__(self):
        """Initialize conversation store"""
        self.logger = logging.getLogger(__name__)

        # Get database URL from environment
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "chatbot")
        user = os.getenv("POSTGRES_USER", "chatbot")
        password = os.getenv("POSTGRES_PASSWORD", "chatbot123")

        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

        self.engine = None
        self.Session = None

    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.logger.info("Connecting to PostgreSQL...")

            # Create engine
            self.engine = create_engine(
                self.database_url,
                poolclass=NullPool,
                echo=False
            )

            # Create tables
            Base.metadata.create_all(self.engine)

            # Create session factory
            self.Session = sessionmaker(bind=self.engine)

            self.logger.info("✅ PostgreSQL connected and tables created")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to conversation history

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Success boolean
        """
        try:
            session = self.Session()

            message = Conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                content=content
            )

            session.add(message)
            session.commit()
            session.close()

            self.logger.debug(f"Saved message to conversation {conversation_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return False

    async def get_conversation(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages (optional)

        Returns:
            List of messages
        """
        try:
            session = self.Session()

            query = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).order_by(Conversation.created_at)

            if limit:
                query = query.limit(limit)

            messages = query.all()
            session.close()

            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]

        except Exception as e:
            self.logger.error(f"Error fetching conversation: {e}")
            return []

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user

        Args:
            user_id: User ID
            limit: Maximum number of conversations

        Returns:
            List of conversations with metadata
        """
        try:
            session = self.Session()

            # Get distinct conversation IDs for user
            conversations = session.query(
                Conversation.conversation_id,
                Conversation.created_at
            ).filter(
                Conversation.user_id == user_id
            ).distinct(
                Conversation.conversation_id
            ).order_by(
                Conversation.created_at.desc()
            ).limit(limit).all()

            session.close()

            return [
                {
                    "conversation_id": conv.conversation_id,
                    "last_activity": conv.created_at.isoformat()
                }
                for conv in conversations
            ]

        except Exception as e:
            self.logger.error(f"Error fetching user conversations: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            session = self.Session()

            session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).delete()

            session.commit()
            session.close()

            self.logger.info(f"Deleted conversation: {conversation_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting conversation: {e}")
            return False

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            session = self.Session()
            session.execute("SELECT 1")
            session.close()
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    async def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")
