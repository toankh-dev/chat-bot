"""
GitLab Controller - Admin-only sync with new schema (simplified).
"""

from fastapi import Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field

from application.services.gitlab_sync_service import GitLabSyncService
from application.services.code_chunking_service import CodeChunkingService
from application.services.kb_sync_service import KBSyncService
from application.services.knowledge_base_service import KnowledgeBaseService
from api.middlewares.jwt_middleware import get_current_user
from core.dependencies import (
    get_document_repository,
    get_embedding_service,
    get_vector_store_service,
    get_test_gitlab_connection_use_case,
    get_fetch_gitlab_repositories_use_case
)
from infrastructure.postgresql.connection.database import get_sync_db_session
from infrastructure.postgresql.connection import get_db_session
from infrastructure.postgresql.repositories.repository_repository import RepositoryRepository
from domain.entities.user import User
from core.config import settings
from core.logger import logger
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# Request/Response Models
# ============================================================================

class SyncRepositoryRequest(BaseModel):
    """Request model for syncing a repository."""
    repository_url: str = Field(..., description="GitLab repository URL (e.g., https://gitlab.com/group/project)")
    chatbot_id: int = Field(..., description="Chatbot ID to link this repository to")
    branch: Optional[str] = Field(default=None, description="Branch to sync (uses default branch if not specified)")
    auto_sync: bool = Field(default=False, description="Auto-sync on GitLab webhook events")


class SyncRepositoryResponse(BaseModel):
    """Response model for repository sync."""
    success: bool
    repository: str
    repository_id: int
    knowledge_base_id: int
    knowledge_base_name: str
    files_processed: int
    files_succeeded: int
    files_failed: int
    total_embeddings: int


class GitLabRepositoryInfo(BaseModel):
    """GitLab repository information from API."""
    id: str
    external_id: str
    name: str
    path: str
    full_name: str
    description: str
    visibility: str
    web_url: str
    http_url_to_repo: str
    default_branch: str
    created_at: str
    last_activity_at: str
    star_count: int
    forks_count: int
    archived: bool
    empty_repo: bool


class GitLabRepositoryListResponse(BaseModel):
    """Response for fetching GitLab repositories."""
    repositories: List[GitLabRepositoryInfo]
    total: int
    page: int
    per_page: int


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
    document_repository = Depends(get_document_repository),
    embedding_service = Depends(get_embedding_service),
    vector_store_service = Depends(get_vector_store_service)
) -> GitLabSyncService:
    """Get GitLab sync service instance."""
    code_chunking_service = CodeChunkingService(max_file_size=50000)

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
    gitlab_sync_service: GitLabSyncService = Depends(get_gitlab_sync_service),
    async_session: AsyncSession = Depends(get_db_session),
    sync_session: Session = Depends(get_sync_db_session)
) -> SyncRepositoryResponse:
    """
    Sync a GitLab repository (Admin only).

    This endpoint:
    1. Extracts project ID/path from repository URL
    2. Fetches repository info from GitLab API
    3. Creates or gets Knowledge Base for the chatbot
    4. Links repository to Knowledge Base
    5. Syncs the repository and creates embeddings for code files

    Args:
        request: Sync request with repository_url and chatbot_id
        current_user: Authenticated admin user
        gitlab_sync_service: GitLab sync service instance
        async_session: Async database session for KB operations
        sync_session: Sync database session for repository operations

    Returns:
        Sync result with statistics
    """
    try:
        logger.info(f"Admin sync for GitLab repository URL: {request.repository_url}")

        # Use GitLab use cases for consistent service management
        # For now, we'll keep using the existing sync service but get the connector through use cases
        from application.services.connector_service import ConnectorService
        connector_service = ConnectorService(sync_session)
        gitlab_connector = connector_service.get_connector_by_provider("gitlab")
        if not gitlab_connector:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitLab connector not configured"
            )
        gitlab_service = connector_service.get_gitlab_service(gitlab_connector)
        logger.info("GitLab service initialized via ConnectorService")

        # Extract project path from URL
        # Example: https://gitlab.com/group/project -> group/project
        try:
            project_path = gitlab_service._extract_project_path(request.repository_url)
            logger.info(f"Extracted project path: {project_path}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid repository URL: {str(e)}"
            )

        # Fetch repository information from GitLab using project path
        try:
            repo_info = gitlab_service.get_project_info(project_path)
            repository_external_id = str(repo_info["id"])
            logger.info(f"Fetched repository: {repo_info['name']} (ID: {repository_external_id})")
        except Exception as e:
            logger.error(f"Failed to fetch repository info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository not found in GitLab: {str(e)}"
            )

        # Use provided branch or default branch from repository
        branch = request.branch if request.branch else repo_info.get("default_branch", "main")

        # Step 1: Create or get Knowledge Base for this repository
        kb_service = KnowledgeBaseService(async_session)
        repo_name = repo_info["name"]

        logger.info(f"Creating/getting Knowledge Base for chatbot {request.chatbot_id}")
        kb_entity = await kb_service.get_or_create_kb_for_repository(
            chatbot_id=request.chatbot_id,
            repo_name=repo_name
        )
        logger.info(f"Knowledge Base: {kb_entity.name} (ID: {kb_entity.id})")

        # Use KB collection ID for vector store
        knowledge_base_id = kb_entity.vector_store_collection or f"kb_{kb_entity.id}"
        group_id = f"group_gitlab_{repository_external_id}"

        logger.info(f"Syncing repository {repo_name} (branch: {branch})")
        logger.info(f"Vector Store Collection: {knowledge_base_id}")

        # Step 2: Sync repository and create embeddings
        result = await gitlab_sync_service.sync_repository_full(
            repository_external_id=repository_external_id,
            knowledge_base_id=knowledge_base_id,
            group_id=group_id,
            user_id=current_user.id,
            branch=branch
        )

        repository_db_id = result.get("repository_id", 0)
        logger.info(f"Repository synced with DB ID: {repository_db_id}")

        # Step 3: Add repository as source to Knowledge Base
        kb_source = await kb_service.add_repository_source(
            knowledge_base_id=kb_entity.id,
            repository_id=str(repository_db_id),
            config={"branch": branch},
            auto_sync=request.auto_sync
        )
        logger.info(f"Created KB source: ID={kb_source.id}, status={kb_source.sync_status}")

        # Step 4: Update source sync status to completed
        await kb_service.update_source_sync_status(
            source_id=kb_source.id,
            status="completed",
            mark_completed=True
        )

        # Step 5: Update repositories table with chatbot_id
        repo_repo = RepositoryRepository(sync_session)
        repository_model = repo_repo.get_by_id(repository_db_id)
        if repository_model:
            repository_model.chatbot_id = request.chatbot_id
            sync_session.commit()
            logger.info(f"Updated repository {repository_db_id} with chatbot_id={request.chatbot_id}")

        return SyncRepositoryResponse(
            success=result.get("success", True),
            repository=result.get("repository", repo_name),
            repository_id=repository_db_id,
            knowledge_base_id=kb_entity.id,
            knowledge_base_name=kb_entity.name,
            files_processed=result.get("files_processed", 0),
            files_succeeded=result.get("files_succeeded", 0),
            files_failed=result.get("files_failed", 0),
            total_embeddings=result.get("total_embeddings", 0)
        )

    except HTTPException:
        raise
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


async def test_gitlab_connection_admin(
    current_user: User = Depends(require_admin),
    use_case = Depends(get_test_gitlab_connection_use_case)
):
    """
    Test GitLab connection using GitLab use cases.
    """
    try:
        result = use_case.execute()

        if result["success"]:
            logger.info(f"GitLab connection test successful: {result['details'].get('user', 'Unknown')}")
            return result["details"]
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

    except Exception as e:
        logger.error(f"GitLab connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitLab connection failed: {str(e)}"
        )


async def fetch_gitlab_repositories_admin(
    visibility: Optional[str] = None,
    owned: bool = False,
    membership: bool = True,
    search: Optional[str] = None,
    order_by: str = "last_activity_at",
    sort: str = "desc",
    per_page: int = 100,
    page: int = 1,
    current_user: User = Depends(require_admin),
    use_case = Depends(get_fetch_gitlab_repositories_use_case)
) -> GitLabRepositoryListResponse:
    """
    Fetch all repositories from GitLab API (Admin only).

    This endpoint fetches repositories from GitLab but does NOT save them to database.
    Use this to browse available repositories before syncing.

    Args:
        visibility: Filter by visibility (public, internal, private)
        owned: Limit to owned projects only
        membership: Limit to projects user is a member of
        search: Search term to filter repositories
        order_by: Sort field (id, name, path, created_at, updated_at, last_activity_at)
        sort: Sort order (asc or desc)
        per_page: Number of results per page (max 100)
        page: Page number
        current_user: Authenticated admin user

    Returns:
        List of GitLab repositories with metadata
    """
    try:
        logger.info(f"Admin fetching GitLab repositories - page {page}, per_page {per_page}")

        # Use GitLab use case to fetch repositories
        result = use_case.execute(per_page=per_page, page=page)
        logger.info("GitLab repositories fetched successfully via GitLab use cases")

        # Transform to response model
        repo_infos = [
            GitLabRepositoryInfo(**repo)
            for repo in result["repositories"]
        ]

        logger.info(f"Returning {len(repo_infos)} repositories to client")

        return GitLabRepositoryListResponse(
            repositories=repo_infos,
            total=len(repo_infos),
            page=page,
            per_page=per_page
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching GitLab repositories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch GitLab repositories: {str(e)}"
        )
