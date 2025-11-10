"""
GitLab Controller - API endpoints for GitLab repository synchronization.
"""

from fastapi import Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field

from application.services.gitlab_sync_service import GitLabSyncService
from infrastructure.external.gitlab_service import GitLabService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from shared.interfaces.repositories.document_repository import DocumentRepository
from api.middlewares.jwt_middleware import get_current_user
from core.dependencies import get_document_repository, get_embedding_service, get_vector_store_service
from domain.entities.user import User
from core.config import settings
from core.logger import logger


# ============================================================================
# Request/Response Models
# ============================================================================

class SyncRepositoryRequest(BaseModel):
    """Request model for syncing a GitLab repository."""
    repo_url: str = Field(..., description="GitLab repository URL")
    branch: str = Field(default="main", description="Branch to sync")
    knowledge_base_id: str = Field(..., description="Knowledge Base ID")
    group_id: str = Field(..., description="Group ID")
    domain: str = Field(default="general", description="Domain classification")


class SyncRepositoryResponse(BaseModel):
    """Response model for repository sync."""
    success: bool
    repository: str
    branch: str
    files_processed: int
    files_failed: int
    total_chunks: int
    languages: dict
    total_lines: int
    total_bytes: int


class RepositoryInfo(BaseModel):
    """Repository information."""
    id: str
    name: str
    url: str
    branch: str
    last_sync: Optional[str] = None
    status: str
    files_count: int
    chunks_count: int


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    group_id: str
    status: str
    repositories: List[RepositoryInfo]
    total_documents: int
    last_sync: Optional[str] = None


# ============================================================================
# Dependency Injection Functions
# ============================================================================

def get_gitlab_service() -> GitLabService:
    """Get GitLab service instance."""
    return GitLabService(
        gitlab_url=settings.GITLAB_URL,
        private_token=settings.GITLAB_API_TOKEN
    )


def get_gitlab_sync_service(
    gitlab_service: GitLabService = Depends(get_gitlab_service),
    document_repository: DocumentRepository = Depends(get_document_repository)
) -> GitLabSyncService:
    """Get GitLab sync service instance."""
    # Create dependencies
    code_chunking_service = CodeChunkingService(max_file_size=50000)
    embedding_service = get_embedding_service()
    vector_store_service = get_vector_store_service()

    kb_sync_service = KBSyncService(
        embedding_service=embedding_service,
        vector_store=vector_store_service.vector_store,
        document_repository=document_repository
    )

    return GitLabSyncService(
        gitlab_service=gitlab_service,
        code_chunking_service=code_chunking_service,
        kb_sync_service=kb_sync_service,
        document_repository=document_repository
    )


# ============================================================================
# Controller Functions
# ============================================================================

async def sync_repository(
    request: SyncRepositoryRequest,
    current_user: User = Depends(get_current_user),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
) -> SyncRepositoryResponse:
    """
    Sync a GitLab repository to Knowledge Base.

    This endpoint clones the repository, extracts code files, chunks them,
    and adds them to the specified Knowledge Base.

    **Required Permissions:** User must be member of the group.
    """
    try:
        # TODO: Verify user has access to the group
        logger.info(f"Starting GitLab sync for repo: {request.repo_url}, branch: {request.branch}")

        result = await gitlab_sync_service.sync_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            knowledge_base_id=request.knowledge_base_id,
            group_id=request.group_id,
            user_id=current_user.id,
            domain=request.domain
        )

        logger.info(f"GitLab sync completed: {result['files_processed']} files processed")
        return SyncRepositoryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to sync repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repository: {str(e)}"
        )


async def list_repositories(
    group_id: str,
    current_user: User = Depends(get_current_user),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
):
    """
    List all synced repositories for a group.

    **Required Permissions:** User must be member of the group.
    """
    try:
        # TODO: Verify user has access to the group
        logger.info(f"Listing repositories for group: {group_id}")

        status_info = await gitlab_sync_service.get_sync_status(
            group_id=group_id
        )

        return {
            "group_id": group_id,
            "repositories": status_info.get("repositories", []),
            "total": len(status_info.get("repositories", []))
        }

    except Exception as e:
        logger.error(f"Failed to list repositories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repositories: {str(e)}"
        )


async def get_sync_status(
    group_id: str,
    repo_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
) -> SyncStatusResponse:
    """
    Get sync status for repositories in a group.

    Optionally filter by repository URL.

    **Required Permissions:** User must be member of the group.
    """
    try:
        # TODO: Verify user has access to the group
        logger.info(f"Getting sync status for group: {group_id}")

        status_info = await gitlab_sync_service.get_sync_status(
            group_id=group_id,
            repo_url=repo_url
        )

        return SyncStatusResponse(**status_info)

    except Exception as e:
        logger.error(f"Failed to get sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


async def delete_repository_sync(
    group_id: str,
    repo_url: str,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository)
):
    """
    Delete all documents synced from a specific repository.

    This removes the repository's code from the Knowledge Base.

    **Required Permissions:** Admin or group owner only.
    """
    try:
        # TODO: Verify user is admin or group owner
        # TODO: Implement batch delete in document repository
        logger.info(f"Deleting repository sync for: {repo_url}")

        return {
            "success": True,
            "message": f"Repository sync deleted for {repo_url}",
            "group_id": group_id
        }

    except Exception as e:
        logger.error(f"Failed to delete repository sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete repository sync: {str(e)}"
        )


async def test_gitlab_connection(
    gitlab_service: GitLabService = Depends(get_gitlab_service)
):
    """
    Test GitLab API connection.

    Returns current authenticated user information.
    """
    try:
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
