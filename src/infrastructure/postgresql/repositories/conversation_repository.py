"""
Conversation repository implementation.

Implements conversation and message data access using SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from infrastructure.postgresql.models import ConversationModel, MessageModel
from shared.interfaces.repositories.conversation_repository import ConversationRepository
from shared.interfaces.repositories.message_repository import MessageRepository


class ConversationRepositoryImpl(ConversationRepository):
    """
    Conversation repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[ConversationModel]:
        """Find conversation by ID."""
        result = await self.session.execute(
            select(ConversationModel).where(ConversationModel.id == id)
        )
        return result.scalar_one_or_none()

    async def find_by_id_with_messages(self, id: int) -> Optional[ConversationModel]:
        """Find conversation by ID with all messages."""
        result = await self.session.execute(
            select(ConversationModel)
            .options(selectinload(ConversationModel.messages))
            .where(ConversationModel.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[ConversationModel]:
        """Find all conversations with pagination."""
        result = await self.session.execute(
            select(ConversationModel).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: ConversationModel) -> ConversationModel:
        """Create new conversation."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ConversationModel) -> ConversationModel:
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
            select(ConversationModel.id).where(ConversationModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ConversationModel]:
        """Find conversations by user ID."""
        result = await self.session.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(desc(ConversationModel.last_message_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_user_and_chatbot(self, user_id: int, chatbot_id: int) -> List[ConversationModel]:
        """Find conversations by user and chatbot."""
        result = await self.session.execute(
            select(ConversationModel)
            .where(
                ConversationModel.user_id == user_id,
                ConversationModel.chatbot_id == chatbot_id
            )
            .order_by(desc(ConversationModel.last_message_at))
        )
        return list(result.scalars().all())


class MessageRepositoryImpl(MessageRepository):
    """
    Message repository implementation with PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: int) -> Optional[MessageModel]:
        """Find message by ID."""
        result = await self.session.execute(
            select(MessageModel).where(MessageModel.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[MessageModel]:
        """Find all messages with pagination."""
        result = await self.session.execute(
            select(MessageModel).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, entity: MessageModel) -> MessageModel:
        """Create new message."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: MessageModel) -> MessageModel:
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
            select(MessageModel.id).where(MessageModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def find_by_conversation(self, conversation_id: int) -> List[MessageModel]:
        """Find all messages in a conversation."""
        result = await self.session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at)
        )
        return list(result.scalars().all())
