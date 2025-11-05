"""
Conversation repository implementation.

Implements conversation and message data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.infrastructure.postgresql.models import Conversation, Message
from src.shared.repositories.base_repository import BaseRepository


class ConversationRepositoryImpl(BaseRepository[Conversation, int]):
    """
    Conversation repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[Conversation]:
        """Find conversation by ID."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == id)
        )
        return result.scalar_one_or_none()

    async def find_by_id_with_messages(self, id: int) -> Optional[Conversation]:
        """Find conversation by ID with all messages."""
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Find all conversations with pagination."""
        result = await self.session.execute(
            select(Conversation).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: Conversation) -> Conversation:
        """Create new conversation."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: Conversation) -> Conversation:
        """Update existing conversation."""
        await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete conversation by ID."""
        conversation = await self.find_by_id(id)
        if conversation:
            await self.session.delete(conversation)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if conversation exists."""
        result = await self.session.execute(
            select(Conversation.id).where(Conversation.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Find conversations by user ID."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.last_message_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_user_and_chatbot(self, user_id: int, chatbot_id: int) -> List[Conversation]:
        """Find conversations by user and chatbot."""
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.chatbot_id == chatbot_id
            )
            .order_by(desc(Conversation.last_message_at))
        )
        return list(result.scalars().all())


class MessageRepositoryImpl(BaseRepository[Message, int]):
    """
    Message repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[Message]:
        """Find message by ID."""
        result = await self.session.execute(
            select(Message).where(Message.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Message]:
        """Find all messages with pagination."""
        result = await self.session.execute(
            select(Message).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: Message) -> Message:
        """Create new message."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: Message) -> Message:
        """Update existing message."""
        await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete message by ID."""
        message = await self.find_by_id(id)
        if message:
            await self.session.delete(message)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: int) -> bool:
        """Check if message exists."""
        result = await self.session.execute(
            select(Message.id).where(Message.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_conversation(self, conversation_id: int) -> List[Message]:
        """Find all messages in a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())
