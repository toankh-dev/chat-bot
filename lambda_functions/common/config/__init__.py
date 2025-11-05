"""
Configuration module for environment-agnostic settings.
Supports both LocalStack (local) and AWS (dev/prod) environments.
"""

from .settings import Settings, get_settings
from .aws_client_factory import AWSClientFactory, create_client
from .client_factory import EventBridgePublisher

__all__ = ['Settings', 'get_settings', 'AWSClientFactory', 'create_client', 'EventBridgePublisher']
