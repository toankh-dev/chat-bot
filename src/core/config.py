"""
Core configuration module for the AI Backend System.

This module centralizes all environment-based configuration including AWS settings,
database connections, JWT secrets, and service endpoints.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic BaseSettings for automatic env var parsing and validation.
    """

    # Application
    APP_NAME: str = "AI Backend System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCOUNT_ID: Optional[str] = None

    # PostgreSQL (RDS)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_backend"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_MAX_CONNECTIONS: int = 20
    POSTGRES_MIN_CONNECTIONS: int = 5

    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # DynamoDB
    DYNAMODB_ENDPOINT: Optional[str] = None  # For local development
    CONVERSATIONS_TABLE: str = "Conversations"
    FEEDBACKS_TABLE: str = "Feedbacks"
    EMBED_INDEX_TABLE: str = "EmbedIndex"
    INGEST_JOBS_TABLE: str = "IngestJobs"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MAX_TOKENS: int = 4096
    BEDROCK_TEMPERATURE: float = 0.7

    # S3
    S3_BUCKET_EMBEDDINGS: str = "ai-backend-embeddings"
    S3_BUCKET_DOCUMENTS: str = "ai-backend-documents"

    # OpenSearch (for vector search)
    OPENSEARCH_ENDPOINT: Optional[str] = None
    OPENSEARCH_INDEX_NAME: str = "documents"

    # WebSocket
    WEBSOCKET_API_ENDPOINT: Optional[str] = None
    CONNECTION_TTL_SECONDS: int = 3600

    # API Gateway
    API_GATEWAY_ENDPOINT: Optional[str] = None
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # External Integrations
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_WORKSPACE_ID: Optional[str] = None

    GITLAB_API_TOKEN: Optional[str] = None
    GITLAB_URL: str = "https://gitlab.com"

    BACKLOG_API_KEY: Optional[str] = None
    BACKLOG_SPACE_KEY: Optional[str] = None
    BACKLOG_DOMAIN: str = "backlog.com"

    # Ingestion
    INGESTION_SCHEDULE_RATE: str = "rate(1 hour)"
    INGESTION_BATCH_SIZE: int = 100

    # Rate Limiting
    RATE_LIMIT_PER_USER: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Singleton settings instance
    """
    return Settings()


# Export settings instance
settings = get_settings()
