import boto3
from botocore.config import Config
from typing import Optional, Dict, Any
import logging

from .settings import get_settings

logger = logging.getLogger(__name__)


class AWSClientFactory:
    """
    Factory class for creating boto3 clients with environment-aware configuration.
    Supports both LocalStack (local) and AWS (dev/prod) environments.
    """

    def __init__(self, settings=None):
        """
        Initialize the factory with settings.

        Args:
            settings: Settings instance. If None, uses global settings.
        """
        self.settings = settings or get_settings()
        self._clients: Dict[str, Any] = {}  # Cache for reusing clients

    def create_client(
        self,
        service_name: str,
        region: Optional[str] = None,
        config: Optional[Config] = None,
        **kwargs
    ):
        """
        Create a boto3 client with environment-specific configuration.

        Args:
            service_name: AWS service name (e.g., 's3', 'dynamodb', 'bedrock-runtime')
            region: AWS region (defaults to settings.aws_region)
            config: Optional botocore.config.Config instance
            **kwargs: Additional arguments passed to boto3.client()

        Returns:
            boto3 client configured for current environment
        """
        # Use provided region or default from settings
        region = region or self.settings.aws_region

        # Create default config if not provided
        if config is None:
            config = self._get_default_config(service_name, region)

        # Build client kwargs
        client_kwargs = {
            'service_name': service_name,
            'config': config,
            **kwargs
        }

        # LocalStack-specific configuration
        if self.settings.is_local:
            client_kwargs.update(self._get_localstack_kwargs(service_name))
            logger.info(f"Creating {service_name} client for LocalStack at {self.settings.aws_endpoint_url}")
        else:
            logger.info(f"Creating {service_name} client for AWS in region {region}")

        # Create and return client
        try:
            client = boto3.client(**client_kwargs)
            logger.debug(f"Successfully created {service_name} client")
            return client
        except Exception as e:
            logger.error(f"Failed to create {service_name} client: {e}")
            raise

    def get_cached_client(self, service_name: str, region: Optional[str] = None):
        """
        Get or create a cached client for the service.
        Useful for Lambda functions to reuse clients across invocations.

        Args:
            service_name: AWS service name
            region: AWS region (defaults to settings.aws_region)

        Returns:
            Cached or newly created boto3 client
        """
        cache_key = f"{service_name}:{region or self.settings.aws_region}"

        if cache_key not in self._clients:
            self._clients[cache_key] = self.create_client(service_name, region)

        return self._clients[cache_key]

    def _get_default_config(self, service_name: str, region: str) -> Config:
        """
        Get default botocore Config with retry and timeout settings.

        Args:
            service_name: AWS service name
            region: AWS region

        Returns:
            botocore.config.Config instance
        """
        # Service-specific timeout configurations
        timeout_configs = {
            'bedrock-runtime': {'connect_timeout': 30, 'read_timeout': 300},
            'lambda': {'connect_timeout': 30, 'read_timeout': 900},
            'opensearchserverless': {'connect_timeout': 10, 'read_timeout': 60},
            's3': {'connect_timeout': 10, 'read_timeout': 60},
            'dynamodb': {'connect_timeout': 5, 'read_timeout': 30},
            'events': {'connect_timeout': 5, 'read_timeout': 30},
        }

        timeouts = timeout_configs.get(service_name, {'connect_timeout': 10, 'read_timeout': 60})

        return Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'  # Adaptive retry mode with exponential backoff
            },
            **timeouts
        )

    def _get_localstack_kwargs(self, service_name: str) -> Dict[str, Any]:
        """
        Get LocalStack-specific client configuration.

        Args:
            service_name: AWS service name

        Returns:
            Dictionary of kwargs for boto3.client()
        """
        kwargs = {
            'endpoint_url': self.settings.aws_endpoint_url,
            'use_ssl': False,
            'verify': False,
            'aws_access_key_id': 'test',  # LocalStack accepts any credentials
            'aws_secret_access_key': 'test',
        }

        # Service-specific endpoint overrides for LocalStack
        # Some services may need different ports or paths
        service_endpoints = {
            # OpenSearch in LocalStack might run on different port
            'opensearchserverless': os.getenv('OPENSEARCH_ENDPOINT', 'http://localhost:9200'),
        }

        if service_name in service_endpoints:
            kwargs['endpoint_url'] = service_endpoints[service_name]

        return kwargs

    def create_resource(
        self,
        service_name: str,
        region: Optional[str] = None,
        **kwargs
    ):
        """
        Create a boto3 resource (higher-level abstraction).

        Args:
            service_name: AWS service name (e.g., 's3', 'dynamodb')
            region: AWS region (defaults to settings.aws_region)
            **kwargs: Additional arguments passed to boto3.resource()

        Returns:
            boto3 resource configured for current environment
        """
        region = region or self.settings.aws_region

        resource_kwargs = {
            'service_name': service_name,
            'region_name': region,
            **kwargs
        }

        # LocalStack-specific configuration
        if self.settings.is_local:
            resource_kwargs.update(self._get_localstack_kwargs(service_name))

        return boto3.resource(**resource_kwargs)


# Import os for environment variable access
import os


# Global factory instance (singleton pattern)
_factory: Optional[AWSClientFactory] = None


def get_factory() -> AWSClientFactory:
    """
    Get global AWS client factory instance.
    Creates singleton on first call.
    """
    global _factory
    if _factory is None:
        _factory = AWSClientFactory()
    return _factory


def create_client(service_name: str, region: Optional[str] = None, **kwargs):
    """
    Convenience function to create a client using the global factory.

    Args:
        service_name: AWS service name
        region: AWS region (optional)
        **kwargs: Additional arguments passed to boto3.client()

    Returns:
        boto3 client configured for current environment

    Example:
        >>> s3_client = create_client('s3')
        >>> dynamodb_client = create_client('dynamodb')
    """
    factory = get_factory()
    return factory.create_client(service_name, region, **kwargs)


def get_cached_client(service_name: str, region: Optional[str] = None):
    """
    Convenience function to get a cached client using the global factory.

    Args:
        service_name: AWS service name
        region: AWS region (optional)

    Returns:
        Cached boto3 client

    Example:
        >>> # In Lambda handler (reuses client across invocations)
        >>> s3_client = get_cached_client('s3')
    """
    factory = get_factory()
    return factory.get_cached_client(service_name, region)
