"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.infrastructure.postgresql.pg_client import Base
from src.core.config import settings


# Override settings for testing
settings.POSTGRES_DB = "ai_backend_test"
settings.ENVIRONMENT = "testing"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.postgres_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "securepassword123"
    }


@pytest.fixture
def sample_chatbot_data():
    """Sample chatbot data for testing."""
    return {
        "name": "Test Bot",
        "description": "A test chatbot for unit testing",
        "system_prompt": "You are a helpful AI assistant for testing purposes",
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "temperature": 0.7,
        "max_tokens": 1000
    }
