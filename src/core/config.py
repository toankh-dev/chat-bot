"""
Core configuration module for the AI Backend System.

This module centralizes all environment-based configuration including AWS settings,
database connections, JWT secrets, and service endpoints.
"""

import os
import json
from typing import Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # PostgreSQL (RDS)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ai_backend"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_MAX_CONNECTIONS: int = 20
    DB_MIN_CONNECTIONS: int = 5

    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    CONVERSATIONS_TABLE: str = "Conversations"
    FEEDBACKS_TABLE: str = "Feedbacks"
    EMBED_INDEX_TABLE: str = "EmbedIndex"
    INGEST_JOBS_TABLE: str = "IngestJobs"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60  # Alias for compatibility

    # AWS Bedrock
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MAX_TOKENS: int = 4096
    BEDROCK_TEMPERATURE: float = 0.7

    # LLM Configuration
    LLM_PROVIDER: str = "bedrock"  # bedrock or gemini
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_MODEL_NAME: str = "gemini-1.5-pro"  # Alias for compatibility

    # Embeddings
    EMBEDDING_PROVIDER: str = "bedrock"  # bedrock or gemini
    EMBEDDING_MODEL: Optional[str] = None  # Auto-detected from provider (e.g., models/embedding-001 for Gemini)
    EMBEDDING_DIMENSION: int = 768  # Default for Gemini, 1536 for Bedrock Titan

    # Vector Store
    VECTOR_STORE_PROVIDER: str = "chromadb"  # chromadb or opensearch

    # ChromaDB Configuration
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_PERSIST_DIRECTORY: str = "./chroma_db"

    # S3
    S3_BUCKET_NAME: str = "ai-backend-documents"
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
    CORS_ORIGINS: Union[str, list[str]] = "http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string or list."""
        if isinstance(v, str):
            # If it's a JSON string, parse it
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Otherwise split by comma
            return [origin.strip() for origin in v.split(",")]
        return v

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


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
