"""
GitLab Controller - Admin-only sync with new schema (simplified).
"""

from fastapi import Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field

from application.services.gitlab_sync_service import GitLabSyncService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from api.middlewares.jwt_middleware import get_current_user
from core.dependencies import get_document_repository, get_embedding_service, get_vector_store_service
from infrastructure.postgresql.connection.database import get_sync_db_session
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from infrastructure.postgresql.repositories.sync_history_repository import SyncHistoryRepository
from domain.entities.user import User
from core.config import settings
from core.logger import logger
from sqlalchemy.orm import Session


# ============================================================================
# Request/Response Models
# ============================================================================

class SyncRepositoryRequest(BaseModel):
    """Request model for syncing a repository."""
    repository_url: str = Field(..., description="GitLab repository URL")
    repository_external_id: str = Field(..., description="GitLab project ID")
    branch: str = Field(default="main", description="Branch to sync")
    knowledge_base_id: str = Field(..., description="Knowledge Base ID")
    group_id: str = Field(..., description="Group ID")


class SyncRepositoryResponse(BaseModel):
    """Response model for repository sync."""
    success: bool
    repository: str
    repository_id: int
    files_processed: int
    files_succeeded: int
    files_failed: int
    total_embeddings: int


class RepositoryInfo(BaseModel):
    """Repository information."""
    id: int
    name: str
    full_name: Optional[str]
    external_id: str
    html_url: Optional[str]
    sync_status: str
    last_synced_at: Optional[str]
    created_at: str


class RepositoryListResponse(BaseModel):
    """Repository list response."""
    repositories: List[RepositoryInfo]
    total: int


class SyncHistoryItem(BaseModel):
    """Sync history item."""
    id: int
    sync_type: str
    status: str
    files_processed: int
    files_succeeded: int
    files_failed: int
    embeddings_created: int
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]


class SyncHistoryResponse(BaseModel):
    """Sync history response."""
    repository_id: int
    repository_name: str
    history: List[SyncHistoryItem]
    total: int


# ============================================================================
# Dependency Injection
# ============================================================================

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require user to be admin."""
    # TODO: Implement proper admin role check
    # For now, just pass through
    return current_user


def get_gitlab_sync_service(
    db_session: Session = Depends(get_sync_db_session),
    document_repository = Depends(get_document_repository)
) -> GitLabSyncService:
    """Get GitLab sync service instance."""
    code_chunking_service = CodeChunkingService(max_file_size=50000)
    embedding_service = get_embedding_service()
    vector_store_service = get_vector_store_service()

    kb_sync_service = KBSyncService(
        embedding_service=embedding_service,
        vector_store=vector_store_service.vector_store,
        document_repository=document_repository
    )

    return GitLabSyncService(
        db_session=db_session,
        code_chunking_service=code_chunking_service,
        kb_sync_service=kb_sync_service,
        document_repository=document_repository
    )


# ============================================================================
# Controller Functions (Admin Only)
# ============================================================================

async def sync_repository_admin(
    request: SyncRepositoryRequest,
    current_user: User = Depends(require_admin),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
) -> SyncRepositoryResponse:
    """
    Sync a GitLab repository (Admin only).

    Uses global GitLab token from settings. Creates embeddings for all code files.
    """
    try:
        logger.info(f"Admin sync for repo {request.repository_external_id}")

        # Use admin's global connection (ID = 1, or create if not exists)
        # This will be the system connection
        result = await gitlab_sync_service.sync_repository_full(
            connection_id=1,  # System/Admin connection
            repository_external_id=request.repository_external_id,
            knowledge_base_id=request.knowledge_base_id,
            group_id=request.group_id,
            user_id=current_user.id,
            branch=request.branch
        )

        return SyncRepositoryResponse(
            success=result.get("success", True),
            repository=result.get("repository", ""),
            repository_id=result.get("repository_id", 0),
            files_processed=result.get("files_processed", 0),
            files_succeeded=result.get("files_succeeded", 0),
            files_failed=result.get("files_failed", 0),
            total_embeddings=result.get("total_embeddings", 0)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to sync repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repository: {str(e)}"
        )


async def list_repositories_admin(
    current_user: User = Depends(require_admin),
    db_session: Session = Depends(get_sync_db_session)
) -> RepositoryListResponse:
    """
    List all synced repositories (Admin only).
    """
    try:
        repo_repo = RepositoryRepository(db_session)

        # Get all repositories for connection_id=1 (system connection)
        repositories = repo_repo.list_by_connection(connection_id=1, only_active=True)

        repo_infos = [
            RepositoryInfo(
                id=repo.id,
                name=repo.name,
                full_name=repo.full_name,
                external_id=repo.external_id,
                html_url=repo.html_url,
                sync_status=repo.sync_status,
                last_synced_at=repo.last_synced_at.isoformat() if repo.last_synced_at else None,
                created_at=repo.created_at.isoformat()
            )
            for repo in repositories
        ]

        return RepositoryListResponse(
            repositories=repo_infos,
            total=len(repo_infos)
        )

    except Exception as e:
        logger.error(f"Failed to list repositories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list repositories"
        )


async def get_repository_sync_history_admin(
    repository_id: int,
    limit: int = 50,
    current_user: User = Depends(require_admin),
    db_session: Session = Depends(get_sync_db_session)
) -> SyncHistoryResponse:
    """
    Get sync history for a repository (Admin only).
    """
    try:
        repo_repo = RepositoryRepository(db_session)
        sync_repo = SyncHistoryRepository(db_session)

        # Get repository
        repository = repo_repo.get_by_id(repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {repository_id} not found"
            )

        # Get sync history
        history = sync_repo.list_by_repository(repository_id, limit=limit)

        history_items = [
            SyncHistoryItem(
                id=sync.id,
                sync_type=sync.sync_type,
                status=sync.status,
                files_processed=sync.files_processed,
                files_succeeded=sync.files_succeeded,
                files_failed=sync.files_failed,
                embeddings_created=sync.embeddings_created,
                started_at=sync.started_at.isoformat(),
                completed_at=sync.completed_at.isoformat() if sync.completed_at else None,
                duration_seconds=sync.duration_seconds
            )
            for sync in history
        ]

        return SyncHistoryResponse(
            repository_id=repository_id,
            repository_name=repository.name,
            history=history_items,
            total=len(history_items)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync history"
        )


async def delete_repository_admin(
    repository_id: int,
    current_user: User = Depends(require_admin),
    db_session: Session = Depends(get_sync_db_session)
):
    """
    Delete repository and all synced data (Admin only).
    """
    try:
        repo_repo = RepositoryRepository(db_session)

        repository = repo_repo.get_by_id(repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {repository_id} not found"
            )

        # Delete repository (CASCADE will delete related records)
        success = repo_repo.delete(repository_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete repository"
            )

        logger.info(f"Admin deleted repository {repository_id}")
        return {
            "success": True,
            "message": f"Repository {repository.name} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete repository"
        )


async def test_gitlab_connection_admin(
    current_user: User = Depends(require_admin)
):
    """
    Test GitLab connection using admin token from settings.
    """
    try:
        from infrastructure.external.gitlab_service import GitLabService

        gitlab_service = GitLabService(
            gitlab_url=settings.GITLAB_URL,
            private_token=settings.GITLAB_API_TOKEN
        )

        user_info = {
            "username": gitlab_service.gl.user.username,
            "name": gitlab_service.gl.user.name,
            "email": gitlab_service.gl.user.email,
            "gitlab_url": gitlab_service.gitlab_url,
            "connection": "success"
        }

        logger.info(f"GitLab connection test successful: {user_info['username']}")
        return user_info

    except Exception as e:
        logger.error(f"GitLab connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitLab connection failed: {str(e)}"
        )
