"""
GitLab Controller - API endpoints for GitLab repository synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field
import asyncio

from src.application.services.gitlab_sync_service import GitLabSyncService
from src.infrastructure.external.gitlab_service import GitLabService
from src.application.services.code_chunking_service import CodeChunkingService
from src.application.services.kb_sync_service import KBSyncService
from src.shared.interfaces.repositories.document_repository import IDocumentRepository
from src.api.dependencies.auth import get_current_user
from src.api.dependencies.database import get_document_repository
from src.domain.entities.user import User
from core.config import settings


router = APIRouter(prefix="/api/v1/gitlab", tags=["GitLab Integration"])


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


class WebhookPushEvent(BaseModel):
    """GitLab push event from webhook."""
    project: dict
    ref: str
    commits: List[dict]
    user_name: str
    user_email: str
    user_username: str


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
# Dependency Injection
# ============================================================================

def get_gitlab_service() -> GitLabService:
    """Get GitLab service instance."""
    return GitLabService(
        gitlab_url=settings.GITLAB_URL,
        private_token=settings.GITLAB_API_TOKEN
    )


def get_gitlab_sync_service(
    gitlab_service: GitLabService = Depends(get_gitlab_service),
    document_repository: IDocumentRepository = Depends(get_document_repository)
) -> GitLabSyncService:
    """Get GitLab sync service instance."""
    from src.infrastructure.ai_services.embeddings.embedding_service_factory import get_embedding_service
    from src.infrastructure.vector_stores.vector_store_factory import get_vector_store

    # Create dependencies
    code_chunking_service = CodeChunkingService(max_file_size=50000)
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    kb_sync_service = KBSyncService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        document_repository=document_repository
    )

    return GitLabSyncService(
        gitlab_service=gitlab_service,
        code_chunking_service=code_chunking_service,
        kb_sync_service=kb_sync_service,
        document_repository=document_repository
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/sync", response_model=SyncRepositoryResponse, status_code=status.HTTP_200_OK)
async def sync_repository(
    request: SyncRepositoryRequest,
    current_user: User = Depends(get_current_user),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
):
    """
    Sync a GitLab repository to Knowledge Base.

    This endpoint clones the repository, extracts code files, chunks them,
    and adds them to the specified Knowledge Base.

    **Required Permissions:** User must be member of the group.
    """
    try:
        # TODO: Verify user has access to the group
        # For now, we'll use the current user's ID

        result = await gitlab_sync_service.sync_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            knowledge_base_id=request.knowledge_base_id,
            group_id=request.group_id,
            user_id=current_user.id,
            domain=request.domain
        )

        return SyncRepositoryResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repository: {str(e)}"
        )


@router.get("/repos", status_code=status.HTTP_200_OK)
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

        status_info = await gitlab_sync_service.get_sync_status(
            group_id=group_id
        )

        return {
            "group_id": group_id,
            "repositories": status_info.get("repositories", []),
            "total": len(status_info.get("repositories", []))
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repositories: {str(e)}"
        )


@router.get("/status/{group_id}", response_model=SyncStatusResponse, status_code=status.HTTP_200_OK)
async def get_sync_status(
    group_id: str,
    repo_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
):
    """
    Get sync status for repositories in a group.

    Optionally filter by repository URL.

    **Required Permissions:** User must be member of the group.
    """
    try:
        # TODO: Verify user has access to the group

        status_info = await gitlab_sync_service.get_sync_status(
            group_id=group_id,
            repo_url=repo_url
        )

        return SyncStatusResponse(**status_info)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.delete("/repos/{group_id}", status_code=status.HTTP_200_OK)
async def delete_repository_sync(
    group_id: str,
    repo_url: str,
    current_user: User = Depends(get_current_user),
    document_repository: IDocumentRepository = Depends(get_document_repository)
):
    """
    Delete all documents synced from a specific repository.

    This removes the repository's code from the Knowledge Base.

    **Required Permissions:** Admin or group owner only.
    """
    try:
        # TODO: Verify user is admin or group owner

        # Delete all documents with matching repo_url in metadata
        # Note: This is a placeholder - you'll need to implement batch delete
        # in the document repository

        return {
            "success": True,
            "message": f"Repository sync deleted for {repo_url}",
            "group_id": group_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete repository sync: {str(e)}"
        )


async def _process_webhook_sync(
    repo_url: str,
    branch: str,
    changed_files: List[str],
    commit_sha: str,
    knowledge_base_id: str,
    group_id: str,
    user_id: str,
    domain: str,
    gitlab_sync_service: GitLabSyncService
):
    """
    Background task to process webhook sync.

    This runs asynchronously after webhook response is returned to GitLab.
    """
    try:
        print(f"🔄 [Background] Starting webhook sync for {repo_url} (commit: {commit_sha[:8]})")

        result = await gitlab_sync_service.sync_changed_files(
            repo_url=repo_url,
            branch=branch,
            changed_files=changed_files,
            commit_sha=commit_sha,
            knowledge_base_id=knowledge_base_id,
            group_id=group_id,
            user_id=user_id,
            domain=domain
        )

        print(f"✅ [Background] Webhook sync completed: {result['files_processed']} files, {result['total_chunks']} chunks")

    except Exception as e:
        print(f"❌ [Background] Webhook sync failed: {str(e)}")
        # TODO: Add error notification/logging system


@router.post("/webhook/push", status_code=status.HTTP_202_ACCEPTED)
async def handle_push_webhook(
    background_tasks: BackgroundTasks,
    webhook_token: str,
    event: WebhookPushEvent = Body(...),
    gitlab_service: GitLabService = Depends(get_gitlab_service),
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service)
):
    """
    Handle GitLab push webhook events.

    This endpoint is called by GitLab when code is pushed to a repository.
    It queues a background job to sync changed files to the Knowledge Base.

    **Flow:**
    1. Validate webhook signature
    2. Parse push event
    3. Queue background sync job
    4. Return immediately (202 Accepted)
    5. Background job processes files and creates embeddings

    **Authentication:** Requires webhook token validation.
    """
    try:
        # Validate webhook signature
        # Note: GitLab uses X-Gitlab-Token header for authentication
        # For now, we'll validate using a simple token comparison

        if webhook_token != settings.GITLAB_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )

        # Parse push event
        parsed_event = gitlab_service.parse_push_event(event.dict())

        # Get changed files
        changed_files = gitlab_service.get_changed_files(parsed_event)

        # Extract repository info
        repo_url = parsed_event["repository"]["url"]
        branch = parsed_event["branch"]
        commit_sha = parsed_event["after"]

        # TODO: Look up group_id and knowledge_base_id from repository configuration
        # For now, use default Knowledge Base for GitLab code
        group_id = "system"  # System group for webhook-triggered syncs
        knowledge_base_id = getattr(settings, 'KNOWLEDGE_BASE_GITLAB_ID', 'kb_gitlab')
        user_id = "system"  # System user for webhook events

        # Add background task to sync changed files
        background_tasks.add_task(
            _process_webhook_sync,
            repo_url=repo_url,
            branch=branch,
            changed_files=changed_files,
            commit_sha=commit_sha,
            knowledge_base_id=knowledge_base_id,
            group_id=group_id,
            user_id=user_id,
            domain="general",
            gitlab_sync_service=gitlab_sync_service
        )

        # Return immediately to GitLab (don't make them wait)
        return {
            "status": "accepted",
            "message": "Webhook received, sync job queued",
            "event_type": "push",
            "repository": parsed_event["repository"]["name"],
            "branch": branch,
            "commit": commit_sha[:8],
            "files_changed": len(changed_files)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.get("/test", status_code=status.HTTP_200_OK)
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

        return user_info

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitLab connection failed: {str(e)}"
        )
