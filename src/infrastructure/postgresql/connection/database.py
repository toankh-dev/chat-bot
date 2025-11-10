"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from core.config import settings
from core.logger import logger


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
    
    def initialize(self):
        """Initialize database engine and session factory."""
        database_url = (
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        # Connect args for asyncpg - disable SSL for local development
        connect_args = {}
        if settings.ENVIRONMENT in ["development", "local"]:
            connect_args = {"ssl": "disable"}

        self.engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args=connect_args
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database connection initialized")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if not self.session_factory:
            self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                # Commit the transaction if no exceptions occurred
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")


# Global instance
db_manager = DatabaseManager()

# Helper function for dependency injection
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async for session in db_manager.get_session():
        yield session