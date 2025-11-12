"""
Connector Service - Centralized connector management with caching.
"""

from typing import Dict, Optional, Any, List
from functools import lru_cache
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from infrastructure.postgresql.models.connector_model import ConnectorModel
from infrastructure.postgresql.models.user_connection_model import UserConnectionModel
from infrastructure.external.gitlab_service import GitLabService
from infrastructure.security.encryption_service import EncryptionService
from core.config import settings
from core.logger import logger


class ConnectorService:
    """
    Centralized service for managing connectors and their configurations.
    
    Features:
    - Connector caching for performance
    - GitLab service creation from connector config
    - Proper error handling and rollback
    - Support for multiple connector instances
    """

    def __init__(self, db_session: Session):
        """
        Initialize connector service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.encryption_service = EncryptionService()
        self._connector_cache: Dict[str, Optional[ConnectorModel]] = {}
        self._gitlab_service_cache: Dict[int, GitLabService] = {}

    def get_connector(self, provider_type: str) -> Optional[ConnectorModel]:
        """
        Get connector by provider type with caching.
        
        Args:
            provider_type: Provider type (gitlab, github, jira, etc.)
            
        Returns:
            ConnectorModel instance or None if not found
        """
        # Check cache first
        if provider_type in self._connector_cache:
            return self._connector_cache[provider_type]

        try:
            # Query database
            connector = self.db_session.query(ConnectorModel).filter(
                ConnectorModel.provider_type == provider_type,
                ConnectorModel.is_active == True
            ).first()

            # Cache result (even None)
            self._connector_cache[provider_type] = connector
            
            if connector:
                logger.info(f"Loaded connector: {connector.name} (type: {provider_type})")
            else:
                logger.warning(f"No active connector found for provider: {provider_type}")

            return connector

        except Exception as e:
            logger.error(f"Failed to get connector for {provider_type}: {str(e)}")
            return None

    def get_or_create_gitlab_connector(self) -> ConnectorModel:
        """
        Get GitLab connector.

        NOTE: This method no longer auto-creates connectors.
        Use POST /api/v1/connectors/gitlab/token to setup connector first.

        Returns:
            ConnectorModel for GitLab

        Raises:
            ValueError: If connector not found
        """
        connector = self.get_connector("gitlab")

        if connector:
            return connector

        # Connector not found - user must setup via API
        logger.error("GitLab connector not found. Please setup connector via POST /api/v1/connectors/gitlab/token")
        raise ValueError(
            "GitLab connector not configured. "
            "Please setup connector via API: POST /api/v1/connectors/gitlab/token"
        )

    def get_gitlab_service(self, connector: Optional[ConnectorModel] = None) -> GitLabService:
        """
        Create GitLab service instance from connector configuration.
        
        Args:
            connector: ConnectorModel instance (optional)
            
        Returns:
            GitLabService configured with connector settings
            
        Raises:
            ValueError: If GitLab configuration is invalid
        """
        # Get connector if not provided
        if connector is None:
            connector = self.get_or_create_gitlab_connector()

        # Check cache
        if connector and connector.id in self._gitlab_service_cache:
            return self._gitlab_service_cache[connector.id]

        try:
            # Get configuration from connector or fallback to settings
            if connector and connector.config_schema:
                config = connector.config_schema
                instance_config = config.get("instance_config", {})
                auth_config = config.get("auth_config", {})
                
                gitlab_url = instance_config.get("gitlab_url", settings.GITLAB_URL if hasattr(settings, 'GITLAB_URL') else "https://gitlab.com")
                
                # Try to get token from connector first (encrypted)
                private_token = None
                if connector.auth_type == "personal_token" and connector.client_id:
                    try:
                        private_token = self.encryption_service.decrypt(connector.client_id)
                        logger.info("Using encrypted token from connector database")
                    except Exception as e:
                        logger.warning(f"Failed to decrypt token from connector: {e}")
                
                # Fallback to environment variable (backward compatibility)
                if not private_token and hasattr(settings, 'GITLAB_API_TOKEN'):
                    private_token = settings.GITLAB_API_TOKEN
                    logger.info("Using token from environment variable (legacy mode)")
                
                logger.info(f"Creating GitLab service from connector config: {gitlab_url}")
            else:
                # Fallback to settings (backward compatibility)
                gitlab_url = settings.GITLAB_URL if hasattr(settings, 'GITLAB_URL') else "https://gitlab.com"
                private_token = settings.GITLAB_API_TOKEN if hasattr(settings, 'GITLAB_API_TOKEN') else None
                
                logger.warning("Using GitLab settings fallback (no connector config)")

            # Validate required settings
            if not gitlab_url:
                raise ValueError("GitLab URL is not configured")
            
            if not private_token:
                raise ValueError("GitLab API token is not configured")

            # Create GitLab service
            gitlab_service = GitLabService(
                gitlab_url=gitlab_url,
                private_token=private_token
            )

            # Cache the service
            if connector and connector.id:
                self._gitlab_service_cache[connector.id] = gitlab_service

            logger.info(f"GitLab service created successfully for: {gitlab_url}")
            return gitlab_service

        except Exception as e:
            logger.error(f"Failed to create GitLab service: {str(e)}")
            raise ValueError(f"Failed to create GitLab service: {str(e)}")

    async def get_or_create_system_connection(
        self, 
        user_id: int, 
        connector: ConnectorModel
    ) -> UserConnectionModel:
        """
        Get or create system connection for admin operations.
        
        Args:
            user_id: Admin user ID
            connector: ConnectorModel instance
            
        Returns:
            UserConnectionModel for system operations
        """
        try:
            # Look for existing system connection
            connection = self.db_session.query(UserConnectionModel).filter(
                UserConnectionModel.user_id == user_id,
                UserConnectionModel.connector_id == connector.id,
                UserConnectionModel.is_active == True
            ).filter(
                UserConnectionModel.connection_metadata.op('->>')('system') == 'true'
            ).first()

            if connection:
                logger.info(f"Using existing system connection: ID={connection.id}")
                return connection

            # Create new system connection
            logger.info(f"Creating system connection for user {user_id} and connector {connector.id}")
            
            connection = UserConnectionModel(
                user_id=user_id,
                connector_id=connector.id,
                is_active=True,
                connection_metadata={
                    "system": True,
                    "created_by": "connector_service",
                    "purpose": "admin_sync_operations",
                    "gitlab_url": settings.GITLAB_URL,
                    "auth_method": "admin_token",
                    "created_at": "auto_generated"
                }
            )

            self.db_session.add(connection)
            self.db_session.commit()
            self.db_session.refresh(connection)

            logger.info(f"Created system connection successfully: ID={connection.id}")
            return connection

        except Exception as e:
            logger.error(f"Failed to create system connection: {str(e)}")
            self.db_session.rollback()
            raise ValueError(f"Failed to create system connection: {str(e)}")

    def get_sync_config(self, connector: ConnectorModel) -> Dict[str, Any]:
        """
        Get sync configuration from connector.
        
        Args:
            connector: ConnectorModel instance
            
        Returns:
            Dictionary with sync configuration
        """
        if not connector or not connector.config_schema:
            # Return default config
            return {
                "batch_size": 10,
                "concurrent_batches": 2,
                "max_file_size_mb": 5,
                "max_retries": 3,
                "retry_delay_seconds": 60
            }

        sync_config = connector.config_schema.get("sync_config", {})
        
        return {
            "batch_size": sync_config.get("default_batch_size", 10),
            "concurrent_batches": sync_config.get("concurrent_batches", 2), 
            "max_file_size_mb": sync_config.get("max_file_size_mb", 5),
            "max_retries": 3,  # From rate_limits
            "retry_delay_seconds": 60,  # From rate_limits
            "include_extensions": sync_config.get("supported_extensions", []),
            "exclude_patterns": sync_config.get("exclude_patterns", [])
        }

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._connector_cache.clear()
        self._gitlab_service_cache.clear()
        logger.info("Connector service caches cleared")

    def refresh_connector(self, provider_type: str) -> Optional[ConnectorModel]:
        """
        Refresh connector cache for specific provider.
        
        Args:
            provider_type: Provider type to refresh
            
        Returns:
            Refreshed ConnectorModel or None
        """
        # Remove from cache
        if provider_type in self._connector_cache:
            del self._connector_cache[provider_type]
            
        # Clear GitLab service cache if needed
        if provider_type == "gitlab":
            self._gitlab_service_cache.clear()

        # Reload from database
        return self.get_connector(provider_type)

    def validate_connector_config(self, connector: ConnectorModel) -> bool:
        """
        Validate connector configuration.
        
        Args:
            connector: ConnectorModel to validate
            
        Returns:
            True if config is valid, False otherwise
        """
        try:
            if not connector.config_schema:
                logger.warning(f"Connector {connector.id} has no config schema")
                return False

            config = connector.config_schema
            
            # Validate GitLab specific config
            if connector.provider_type == "gitlab":
                gitlab_url = config.get("gitlab_url")
                if not gitlab_url or not gitlab_url.startswith(("http://", "https://")):
                    logger.error(f"Invalid GitLab URL in connector {connector.id}: {gitlab_url}")
                    return False

            logger.info(f"Connector {connector.id} configuration is valid")
            return True

        except Exception as e:
            logger.error(f"Failed to validate connector {connector.id} config: {str(e)}")
            return False

    def setup_gitlab_personal_token_connector(
        self,
        name: str,
        gitlab_url: str,
        admin_token: Optional[str] = None
    ) -> ConnectorModel:
        """
        Setup GitLab connector with personal access token.
        This method is idempotent - it will update existing connector or create new one.
        The connector ID will remain stable across multiple calls.

        Args:
            name: Connector display name
            gitlab_url: GitLab instance URL
            admin_token: Personal access token (optional, uses env if not provided)

        Returns:
            ConnectorModel with stable ID
        """
        try:
            # Validate GitLab URL
            if not gitlab_url.startswith(("http://", "https://")):
                raise ValueError("GitLab URL must start with http:// or https://")

            # Encrypt admin token if provided
            encrypted_admin_token = None
            if admin_token:
                encrypted_admin_token = self.encryption_service.encrypt(admin_token)

            # Build config schema
            config_schema = {
                "instance_config": {
                    "gitlab_url": gitlab_url.rstrip('/'),
                    "api_version": "v4",
                    "timeout_seconds": 30,
                    "verify_ssl": True
                },
                "auth_config": {
                    "primary_method": "personal_token",
                    "supported_methods": ["personal_token"],
                    "personal_token": {
                        "source": "database" if admin_token else "environment",
                        "env_var": "GITLAB_API_TOKEN",
                        "fallback_enabled": True
                    }
                },
                "sync_config": {
                    "default_batch_size": 10,
                    "max_file_size_mb": 5,
                    "concurrent_batches": 2,
                    "max_retries": 3,
                    "retry_delay_seconds": 60
                },
                "rate_limits": {
                    "requests_per_minute": 300,
                    "requests_per_hour": 2000,
                    "burst_limit": 10
                },
                "features": {
                    "repository_sync": True,
                    "incremental_sync": True,
                    "webhook_support": False,
                    "admin_only": True
                },
                "legacy_mode": {
                    "enabled": not bool(admin_token),
                    "env_token_fallback": True,
                    "auto_created": False
                }
            }

            # Check if connector already exists
            existing = self.get_connector("gitlab")

            if existing:
                # UPDATE existing connector (keeps same ID)
                logger.info(f"Updating existing GitLab connector: ID={existing.id}")

                existing.name = name
                existing.client_id = encrypted_admin_token
                existing.config_schema = config_schema
                existing.is_active = True
                existing.updated_at = datetime.utcnow()

                self.db_session.commit()
                self.db_session.refresh(existing)

                # Clear and update caches
                self._connector_cache.pop("gitlab", None)
                if existing.id in self._gitlab_service_cache:
                    del self._gitlab_service_cache[existing.id]
                self._connector_cache["gitlab"] = existing

                logger.info(f"✓ Updated GitLab connector: ID={existing.id} (stable), URL={gitlab_url}")
                return existing

            # CREATE new connector
            connector = ConnectorModel(
                name=name,
                provider_type="gitlab",
                auth_type="personal_token",
                client_id=encrypted_admin_token,
                client_secret=None,
                config_schema=config_schema,
                is_active=True
            )

            self.db_session.add(connector)
            self.db_session.commit()
            self.db_session.refresh(connector)

            # Update cache
            self._connector_cache["gitlab"] = connector

            logger.info(f"✓ Created new GitLab connector: ID={connector.id}, URL={gitlab_url}")
            return connector
            
        except Exception as e:
            logger.error(f"Failed to setup GitLab personal token connector: {e}")
            self.db_session.rollback()
            raise ValueError(f"Failed to setup GitLab personal token connector: {e}")

    def get_decrypted_credentials(self, connector: ConnectorModel) -> Dict[str, str]:
        """
        Get decrypted credentials from connector.
        
        Args:
            connector: ConnectorModel instance
            
        Returns:
            Dictionary with decrypted credentials (personal token only)
        """
        credentials = {}
        
        try:
            if connector.auth_type == "personal_token":
                if connector.client_id:  # Token stored in client_id field
                    credentials["personal_token"] = self.encryption_service.decrypt(connector.client_id)
            else:
                logger.warning(f"Unsupported auth type {connector.auth_type} for connector {connector.id}")
                    
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for connector {connector.id}: {e}")
            
        return credentials

    def update_connector_credentials(
        self,
        connector_id: int,
        personal_token: str
    ) -> ConnectorModel:
        """
        Update connector personal token credentials.
        
        Args:
            connector_id: Connector ID to update
            personal_token: New personal token
            
        Returns:
            Updated ConnectorModel
        """
        try:
            connector = self.db_session.query(ConnectorModel).filter(
                ConnectorModel.id == connector_id
            ).first()
            
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            if connector.auth_type != "personal_token":
                raise ValueError(f"Connector {connector_id} is not using personal token authentication")
            
            # Encrypt and store the personal token
            connector.client_id = self.encryption_service.encrypt(personal_token)
            
            self.db_session.commit()
            self.db_session.refresh(connector)
            
            # Clear caches
            self._connector_cache.pop(connector.provider_type, None)
            self._gitlab_service_cache.pop(connector_id, None)
            
            logger.info(f"Updated credentials for connector {connector_id}")
            return connector
            
        except Exception as e:
            logger.error(f"Failed to update connector credentials: {e}")
            self.db_session.rollback()
            raise ValueError(f"Failed to update credentials: {e}")

    def test_connector_credentials(self, connector: ConnectorModel) -> Dict[str, Any]:
        """
        Test connector credentials by attempting to connect.
        
        Args:
            connector: ConnectorModel to test
            
        Returns:
            Dictionary with test results
        """
        try:
            if connector.provider_type == "gitlab":
                gitlab_service = self.get_gitlab_service(connector)
                
                # Test connection by getting user info
                user_info = {
                    "username": gitlab_service.gl.user.username,
                    "name": gitlab_service.gl.user.name,
                    "email": gitlab_service.gl.user.email,
                    "gitlab_url": gitlab_service.gitlab_url
                }
                
                return {
                    "success": True,
                    "connector_id": connector.id,
                    "auth_type": connector.auth_type,
                    "user_info": user_info,
                    "message": "Connection successful"
                }
                
        except Exception as e:
            logger.error(f"Connector test failed for {connector.id}: {e}")
            return {
                "success": False,
                "connector_id": connector.id,
                "auth_type": connector.auth_type,
                "error": str(e),
                "message": "Connection failed"
            }

    def list_all_connectors(self) -> List[ConnectorModel]:
        """
        Get all connectors from database.
        
        Returns:
            List of all ConnectorModel instances
        """
        try:
            return self.db_session.query(ConnectorModel).all()
        except Exception as e:
            logger.error(f"Failed to list connectors: {e}")
            raise ValueError(f"Failed to retrieve connectors: {e}")

    def get_connector_by_provider(self, provider_type: str) -> Optional[ConnectorModel]:
        """
        Get connector by provider type (alias for get_connector).
        
        Args:
            provider_type: Provider type (gitlab, github, jira, etc.)
            
        Returns:
            ConnectorModel instance or None if not found
        """
        return self.get_connector(provider_type)

    def get_connector_by_id(self, connector_id: int) -> Optional[ConnectorModel]:
        """
        Get connector by ID.
        
        Args:
            connector_id: Connector ID to retrieve
            
        Returns:
            ConnectorModel or None if not found
        """
        try:
            return self.db_session.query(ConnectorModel).filter(
                ConnectorModel.id == connector_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get connector {connector_id}: {e}")
            return None

    def get_active_connections_count(self, connector_id: int) -> int:
        """
        Get count of active user connections for a connector.

        Args:
            connector_id: Connector ID to check

        Returns:
            Number of active connections
        """
        try:
            return self.db_session.query(UserConnectionModel).filter(
                UserConnectionModel.connector_id == connector_id,
                UserConnectionModel.is_active == True
            ).count()
        except Exception as e:
            logger.error(f"Failed to count active connections for connector {connector_id}: {e}")
            return 0

    def delete_connector(self, connector_id: int) -> None:
        """
        Delete a connector and all its user connections.

        Args:
            connector_id: Connector ID to delete

        Raises:
            ValueError: If connector not found or deletion fails
        """
        try:
            connector = self.get_connector_by_id(connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")

            # Delete all user connections first
            self.db_session.query(UserConnectionModel).filter(
                UserConnectionModel.connector_id == connector_id
            ).delete()

            # Delete the connector
            self.db_session.delete(connector)
            self.db_session.commit()

            # Clear caches
            self._connector_cache.pop(connector.provider_type, None)
            self._gitlab_service_cache.pop(connector_id, None)

            logger.info(f"Successfully deleted connector {connector_id} and its connections")

        except Exception as e:
            logger.error(f"Failed to delete connector {connector_id}: {e}")
            self.db_session.rollback()
            raise ValueError(f"Failed to delete connector: {e}")