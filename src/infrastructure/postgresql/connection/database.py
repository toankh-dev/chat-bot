"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator
from core.config import settings
from core.logger import logger


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.sync_engine = None
        self.sync_session_factory = None

    def initialize(self):
        """Initialize database engine and session factory."""
        # Async engine
        database_url = (
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        self.engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Sync engine for non-async operations
        sync_database_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        self.sync_engine = create_engine(
            sync_database_url,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self.sync_session_factory = sessionmaker(
            self.sync_engine,
            class_=Session,
            expire_on_commit=False
        )

        logger.info("Database connection initialized (async + sync)")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    def get_sync_session(self) -> Generator[Session, None, None]:
        """Get sync database session."""
        if not self.sync_session_factory:
            self.initialize()

        session = self.sync_session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed (async)")
        if self.sync_engine:
            self.sync_engine.dispose()
            logger.info("Database connections closed (sync)")


# Global instance
db_manager = DatabaseManager()

# Helper functions for dependency injection
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection."""
    async for session in db_manager.get_session():
        yield session


def get_sync_db_session() -> Generator[Session, None, None]:
    """Get sync database session for dependency injection."""
    yield from db_manager.get_sync_session()