"""
PostgreSQL client using SQLAlchemy for async operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime
from typing import AsyncGenerator
from src.core.config import settings
from src.core.logger import logger

# SQLAlchemy Base
Base = declarative_base()


# Association Tables for Many-to-Many relationships
user_roles_table = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', PGUUID(as_uuid=False), ForeignKey('users.id'), primary_key=True),
    Column('role_id', PGUUID(as_uuid=False), ForeignKey('roles.id'), primary_key=True),
    Column('workspace_id', PGUUID(as_uuid=False), ForeignKey('workspaces.id')),
    Column('created_at', DateTime, default=datetime.utcnow)
)


# ORM Models
class UserModel(Base):
    """User ORM model."""
    __tablename__ = 'users'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)


class RoleModel(Base):
    """Role ORM model."""
    __tablename__ = 'roles'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    permissions = Column(JSON, default=list)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkspaceModel(Base):
    """Workspace ORM model."""
    __tablename__ = 'workspaces'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    owner_id = Column(PGUUID(as_uuid=False), ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatbotModel(Base):
    """Chatbot ORM model."""
    __tablename__ = 'chatbots'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    workspace_id = Column(PGUUID(as_uuid=False), ForeignKey('workspaces.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    model_id = Column(String(255), nullable=False)
    temperature = Column(Integer, default=70)  # Store as integer (0-100)
    max_tokens = Column(Integer, default=4096)
    tools = Column(JSON, default=list)  # Store tool IDs as JSON array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionModel(Base):
    """Conversation session ORM model."""
    __tablename__ = 'sessions'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    user_id = Column(PGUUID(as_uuid=False), ForeignKey('users.id'), nullable=False)
    chatbot_id = Column(PGUUID(as_uuid=False), ForeignKey('chatbots.id'), nullable=False)
    title = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ToolModel(Base):
    """Tool registry ORM model."""
    __tablename__ = 'tools'

    id = Column(PGUUID(as_uuid=False), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    tool_type = Column(String(50), nullable=False)  # web_search, gitlab, backlog, etc.
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostgreSQLClient:
    """
    PostgreSQL client for async database operations.

    Manages database connections and provides session management.
    """

    def __init__(self):
        """Initialize PostgreSQL client."""
        self.engine = create_async_engine(
            settings.postgres_url,
            echo=settings.DEBUG,
            pool_size=settings.POSTGRES_MAX_CONNECTIONS,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("PostgreSQL client initialized")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session.

        Yields:
            AsyncSession: Database session

        Usage:
            async with client.get_session() as session:
                # Use session here
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self):
        """Drop all database tables (use with caution)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("PostgreSQL client closed")


# Singleton instance
_pg_client = None


def get_postgresql_client() -> PostgreSQLClient:
    """Get singleton PostgreSQL client instance."""
    global _pg_client
    if _pg_client is None:
        _pg_client = PostgreSQLClient()
    return _pg_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    client = get_postgresql_client()
    async with client.get_session() as session:
        yield session
