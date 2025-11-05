import os
from typing import Optional, Dict, Any
from enum import Enum


class Environment(str, Enum):
    """Supported deployment environments."""
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Settings:
    """
    Unified settings class for all environments.
    Loads configuration from environment variables.
    """

    def __init__(self):
        # Core environment settings
        self.environment = Environment(os.getenv('ENVIRONMENT', 'local'))
        self.project_name = os.getenv('PROJECT_NAME', 'kass-chatbot')
        self.aws_region = os.getenv('AWS_REGION', os.getenv('REGION', 'us-east-1'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # AWS service endpoints (LocalStack vs AWS)
        self.aws_endpoint_url = self._get_aws_endpoint()
        self.use_ssl = self.environment != Environment.LOCAL

        # DynamoDB configuration
        self.conversations_table = os.getenv(
            'CONVERSATIONS_TABLE',
            f'{self.project_name}-{self.environment.value}-conversations'
        )
        self.agent_state_table = os.getenv(
            'AGENT_STATE_TABLE',
            f'{self.project_name}-{self.environment.value}-agent-state'
        )
        self.tool_logs_table = os.getenv(
            'TOOL_LOGS_TABLE',
            f'{self.project_name}-{self.environment.value}-tool-logs'
        )

        # S3 configuration
        self.documents_bucket = os.getenv(
            'DOCUMENTS_BUCKET',
            f'{self.project_name}-{self.environment.value}-documents'
        )
        self.embeddings_bucket = os.getenv(
            'EMBEDDINGS_BUCKET',
            f'{self.project_name}-{self.environment.value}-embeddings'
        )
        self.logs_bucket = os.getenv(
            'LOGS_BUCKET',
            f'{self.project_name}-{self.environment.value}-logs'
        )
        self.backups_bucket = os.getenv(
            'BACKUPS_BUCKET',
            f'{self.project_name}-{self.environment.value}-backups'
        )

        # OpenSearch configuration
        self.opensearch_endpoint = os.getenv('OPENSEARCH_ENDPOINT', self._get_default_opensearch_endpoint())
        self.opensearch_collection_id = os.getenv('OPENSEARCH_COLLECTION_ID', '')
        self.opensearch_index = os.getenv('OPENSEARCH_INDEX', 'documents')

        # LLM Provider configuration
        self.llm_provider = os.getenv('LLM_PROVIDER', self._get_default_llm_provider())

        # Bedrock configuration (AWS)
        self.bedrock_model_id = os.getenv(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        )
        self.bedrock_embed_model_id = os.getenv(
            'BEDROCK_EMBED_MODEL_ID',
            'amazon.titan-embed-text-v2:0'
        )

        # Gemini configuration (Local)
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        self.gemini_embed_model = os.getenv('GEMINI_EMBED_MODEL', 'models/text-embedding-004')

        # EventBridge configuration
        self.eventbus_name = os.getenv(
            'EVENTBUS_NAME',
            f'{self.project_name}-{self.environment.value}-events'
        )

    def _get_aws_endpoint(self) -> Optional[str]:
        """Get AWS endpoint URL based on environment."""
        if self.environment == Environment.LOCAL:
            return os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
        return None  # Use default AWS endpoints

    def _get_default_opensearch_endpoint(self) -> str:
        """Get default OpenSearch endpoint based on environment."""
        if self.environment == Environment.LOCAL:
            return os.getenv('OPENSEARCH_ENDPOINT', 'http://localhost:9200')
        return ''  # Will be provided by Terraform in AWS

    def _get_default_llm_provider(self) -> str:
        """Get default LLM provider based on environment."""
        if self.environment == Environment.LOCAL:
            return 'gemini'
        return 'bedrock'

    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == Environment.LOCAL

    @property
    def is_aws(self) -> bool:
        """Check if running in AWS environment."""
        return self.environment in [Environment.DEV, Environment.PROD]

    def get_table_name(self, table_type: str) -> str:
        """Get DynamoDB table name by type."""
        table_map = {
            'conversations': self.conversations_table,
            'agent_state': self.agent_state_table,
            'tool_logs': self.tool_logs_table,
        }
        return table_map.get(table_type, '')

    def get_bucket_name(self, bucket_type: str) -> str:
        """Get S3 bucket name by type."""
        bucket_map = {
            'documents': self.documents_bucket,
            'embeddings': self.embeddings_bucket,
            'logs': self.logs_bucket,
            'backups': self.backups_bucket,
        }
        return bucket_map.get(bucket_type, '')

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for logging/debugging."""
        return {
            'environment': self.environment.value,
            'project_name': self.project_name,
            'aws_region': self.aws_region,
            'aws_endpoint_url': self.aws_endpoint_url,
            'llm_provider': self.llm_provider,
            'opensearch_endpoint': self.opensearch_endpoint,
            'conversations_table': self.conversations_table,
            'documents_bucket': self.documents_bucket,
        }


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance.
    Creates singleton on first call.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
