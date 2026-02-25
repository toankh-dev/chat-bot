"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from src.infrastructure.postgresql.models import Base
from unittest.mock import patch
from src.core.config import settings
from tests.mocks.s3_service_mock import S3FileStorageServiceMock
from src.infrastructure.s3.s3_file_storage_service import S3FileStorageService


# Override settings for testing
settings.DB_NAME = "ai_backend_test"
settings.ENVIRONMENT = "testing"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine(event_loop):
    """Create a test database engine."""
    # Drop existing test database first
    old_db_name = settings.DB_NAME
    settings.DB_NAME = "postgres"  # Connect to default db to drop test db
    engine = create_async_engine(
        settings.postgres_url,
        isolation_level="AUTOCOMMIT",  # Required for database operations
        echo=False,
        pool_pre_ping=True,
    )
    try:
        async with engine.connect() as conn:
            # Wait for all connections to close
            await conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{old_db_name}'
                AND pid <> pg_backend_pid()
            """))
            await conn.execute(text(f"DROP DATABASE IF EXISTS {old_db_name}"))
            await conn.execute(text(f"CREATE DATABASE {old_db_name}"))
            await conn.commit()
    finally:
        await engine.dispose()

    # Set back test database name and create tables
    settings.DB_NAME = old_db_name
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
def s3_service():
    """Mock S3 service for testing."""
    s3_mock = S3FileStorageServiceMock()
    with patch.object(S3FileStorageService, '__new__', return_value=s3_mock):
        yield s3_mock

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
