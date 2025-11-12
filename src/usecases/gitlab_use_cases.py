"""
GitLab use cases for repository management and synchronization.
Handles business logic for GitLab operations.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.gitlab_sync_service import GitLabSyncService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.knowledge_base_service import KnowledgeBaseService
from application.services.connector_service import ConnectorService
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository

logger = logging.getLogger(__name__)


class GitLabUseCases:
    """
    Use cases for GitLab repository management and synchronization.
    Encapsulates business logic for GitLab operations.
    """
    
    def __init__(
        self, 
        sync_session: Session, 
        async_session: AsyncSession,
        document_repository,
        embedding_service, 
        vector_store_service
    ):
        self.sync_session = sync_session
        self.async_session = async_session
        self.document_repository = document_repository
        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service
        self.connector_service = ConnectorService(sync_session)
    
    def get_gitlab_sync_service(self) -> GitLabSyncService:
        """
        Create and configure GitLab sync service with all dependencies.
        
        Returns:
            Configured GitLabSyncService instance
        """
        try:
            # Initialize services with dependencies
            repository_repo = RepositoryRepository(self.sync_session)
            sync_history_repo = SyncHistoryRepository(self.sync_session)
            code_chunking_service = CodeChunkingService(max_file_size=50000)
            
            kb_sync_service = KBSyncService(
                document_repository=self.document_repository,
                embedding_service=self.embedding_service,
                vector_store_service=self.vector_store_service
            )
            
            return GitLabSyncService(
                repository_repo=repository_repo,
                sync_history_repo=sync_history_repo,
                code_chunking_service=code_chunking_service,
                kb_sync_service=kb_sync_service
            )
            
        except Exception as e:
            logger.error(f"Failed to create GitLab sync service: {e}")
            raise ValueError(f"Failed to initialize GitLab sync service: {e}")
    
    def test_gitlab_connection(self) -> Dict[str, Any]:
        """
        Test GitLab connectivity using the configured connector.
        
        Returns:
            Test result with connection status and details
        """
        try:
            # Get GitLab connector
            gitlab_connector = self.connector_service.get_connector_by_provider("gitlab")
            if not gitlab_connector or not gitlab_connector.is_active:
                return {
                    "success": False,
                    "message": "GitLab connector not found or not active",
                    "details": {}
                }
            
            # Test connection
            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)
            
            # Try to get user info to test connection
            try:
                user_info = gitlab_service.get_current_user()
                return {
                    "success": True,
                    "message": "GitLab connection successful",
                    "details": {
                        "user": user_info.get("username", "Unknown"),
                        "gitlab_url": gitlab_connector.config_schema.get("instance_config", {}).get("gitlab_url"),
                        "connector_id": gitlab_connector.id
                    }
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"GitLab connection failed: {str(e)}",
                    "details": {"error": str(e)}
                }
                
        except Exception as e:
            logger.error(f"Failed to test GitLab connection: {e}")
            return {
                "success": False,
                "message": f"Failed to test GitLab connection: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def fetch_repositories(self, per_page: int = 20, page: int = 1) -> Dict[str, Any]:
        """
        Fetch repositories from GitLab.
        
        Args:
            per_page: Number of repositories per page
            page: Page number to fetch
            
        Returns:
            Repository list with pagination info
        """
        try:
            # Get GitLab connector and service
            gitlab_connector = self.connector_service.get_connector_by_provider("gitlab")
            if not gitlab_connector or not gitlab_connector.is_active:
                raise ValueError("GitLab connector not found or not active")
            
            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)
            
            # Fetch repositories
            repositories = gitlab_service.get_projects(per_page=per_page, page=page)
            
            return {
                "success": True,
                "repositories": repositories,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": len(repositories) if repositories else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            raise ValueError(f"Failed to fetch repositories: {e}")
    
    def sync_repository(
        self, 
        repository_id: int, 
        branch: str = "main", 
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize a specific repository.
        
        Args:
            repository_id: GitLab repository ID
            branch: Branch to sync (default: main)
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            Synchronization result
        """
        try:
            sync_service = self.get_gitlab_sync_service()
            
            # Get GitLab connector and service
            gitlab_connector = self.connector_service.get_connector_by_provider("gitlab")
            if not gitlab_connector or not gitlab_connector.is_active:
                raise ValueError("GitLab connector not found or not active")
            
            gitlab_service = self.connector_service.get_gitlab_service(gitlab_connector)
            
            # Perform sync
            result = sync_service.sync_repository(
                gitlab_service=gitlab_service,
                repository_id=repository_id,
                branch=branch,
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or []
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync repository {repository_id}: {e}")
            raise ValueError(f"Failed to sync repository: {e}")
    
    def get_repositories(
        self, 
        page: int = 1, 
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get stored repositories with pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            Repository list with pagination
        """
        try:
            sync_service = self.get_gitlab_sync_service()
            repositories = sync_service.get_repositories(page=page, per_page=per_page)
            
            return {
                "repositories": repositories,
                "pagination": {
                    "page": page,
                    "per_page": per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get repositories: {e}")
            raise ValueError(f"Failed to get repositories: {e}")
    
    def get_repository_details(self, repository_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a repository.
        
        Args:
            repository_id: Repository ID
            
        Returns:
            Repository details
        """
        try:
            sync_service = self.get_gitlab_sync_service()
            repository = sync_service.get_repository_by_id(repository_id)
            
            if not repository:
                raise ValueError(f"Repository {repository_id} not found")
            
            return {
                "repository": repository,
                "sync_history": sync_service.get_sync_history(repository_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository details: {e}")
            raise ValueError(f"Failed to get repository details: {e}")
    
    def get_repository_history(
        self, 
        repository_id: int, 
        page: int = 1, 
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get synchronization history for a repository.
        
        Args:
            repository_id: Repository ID
            page: Page number
            per_page: Items per page
            
        Returns:
            Sync history with pagination
        """
        try:
            sync_service = self.get_gitlab_sync_service()
            history = sync_service.get_sync_history(
                repository_id=repository_id,
                page=page,
                per_page=per_page
            )
            
            return {
                "history": history,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "repository_id": repository_id
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get repository history: {e}")
            raise ValueError(f"Failed to get repository history: {e}")
    
    async def setup_knowledge_base_for_repository(self, repository_id: int) -> Dict[str, Any]:
        """
        Set up knowledge base for a specific repository.
        
        Args:
            repository_id: Repository ID
            
        Returns:
            Setup result
        """
        try:
            kb_service = KnowledgeBaseService(self.async_session)
            result = await kb_service.setup_repository_knowledge_base(repository_id)
            
            return {
                "success": True,
                "knowledge_base_id": result.get("knowledge_base_id"),
                "message": "Knowledge base setup completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to setup knowledge base for repository {repository_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to setup knowledge base: {str(e)}",
                "error": str(e)
            }