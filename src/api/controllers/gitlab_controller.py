"""
GitLab Controller - Admin-only sync with clean architecture.
"""

from fastapi import Depends, HTTPException, status
from typing import List

from schemas.gitlab_schema import (
    SyncRepositoryRequest,
    SyncRepositoryResponse,
    GitLabRepositoryInfo,
    GitLabRepositoryListResponse,
    GitLabConnectionTestResponse
)

from api.middlewares.jwt_middleware import require_admin
from core.dependencies import (
    get_test_gitlab_connection_use_case,
    get_fetch_gitlab_repositories_use_case,
    get_sync_repository_use_case
)
from domain.entities.user import UserEntity
from core.logger import logger

# ============================================================================
# Controller Functions (Admin Only)
# ============================================================================

async def sync_repository_admin(
    request: SyncRepositoryRequest,
    current_user: UserEntity = Depends(require_admin),
    sync_repository_use_case = Depends(get_sync_repository_use_case)
) -> SyncRepositoryResponse:
    """
    Sync a GitLab repository (Admin only).

    This endpoint uses the SyncRepositoryUseCase to handle all business logic
    for syncing GitLab repositories with knowledge bases.

    Args:
        request: Sync request with repository_url and chatbot_id
        current_user: Authenticated admin user
        sync_repository_use_case: Use case for repository synchronization

    Returns:
        Sync result with statistics
    """
    try:
        logger.info(f"Admin sync for GitLab repository URL: {request.repository_url}")
        
        # Execute the sync repository use case
        result = await sync_repository_use_case.execute(request, current_user.id)
        
        return SyncRepositoryResponse(
            success=result["success"],
            repository=result["repository_name"],
            repository_id=result["repository_id"],
            knowledge_base_id=result["knowledge_base_id"],
            knowledge_base_name=result["knowledge_base_name"],
            files_processed=result["files_processed"],
            files_succeeded=result["files_succeeded"],
            files_failed=result["files_failed"],
            total_embeddings=result["total_embeddings"]
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
    current_user: UserEntity = Depends(require_admin),
    test_gitlab_connection_use_case = Depends(get_test_gitlab_connection_use_case)
) -> GitLabConnectionTestResponse:
    """
    Test GitLab connection using GitLab use cases.
    
    Returns:
        GitLab connection test result with user information
    """
    try:
        result = test_gitlab_connection_use_case.execute()

        if result["success"]:
            logger.info(f"GitLab connection test successful: {result['details'].get('user', 'Unknown')}")
            
            # Convert to response schema
            details = result["details"]
            return GitLabConnectionTestResponse(
                success=True,
                user_id=str(details.get("id", "")),
                username=details.get("username"),
                name=details.get("name"),
                email=details.get("email"),
                message="Connection successful"
            )
        else:
            return GitLabConnectionTestResponse(
                success=False,
                message=result["message"]
            )

    except Exception as e:
        logger.error(f"GitLab connection failed: {str(e)}")
        return GitLabConnectionTestResponse(
            success=False,
            message=f"GitLab connection failed: {str(e)}"
        )


async def fetch_gitlab_repositories_admin(
    connector_id: int,
    current_user: UserEntity = Depends(require_admin),
    fetch_gitlab_repositories_use_case = Depends(get_fetch_gitlab_repositories_use_case)
) -> GitLabRepositoryListResponse:
    """
    Fetch all repositories from GitLab API using a specific connector (Admin only).

    This endpoint fetches repositories from GitLab but does NOT save them to database.
    Use this to browse available repositories before syncing.

    Args:
        connector_id: GitLab connector ID to use for fetching repositories
        current_user: Authenticated admin user
        fetch_gitlab_repositories_use_case: Use case for fetching repositories

    Returns:
        List of GitLab repositories with metadata
    """
    try:
        # Use GitLab use case to fetch all repositories with specific connector
        result = fetch_gitlab_repositories_use_case.execute(
            connector_id=connector_id
        )

        # Transform to response model
        repo_infos = [
            GitLabRepositoryInfo(**repo)
            for repo in result["repositories"]
        ]

        logger.info(f"Returning {len(repo_infos)} repositories to client")

        return GitLabRepositoryListResponse(
            repositories=repo_infos,
            total=len(repo_infos),
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
