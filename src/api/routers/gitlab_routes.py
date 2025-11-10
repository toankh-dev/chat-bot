"""
GitLab Routes - Admin-only repository sync (simplified).
"""

from fastapi import APIRouter, status

from api.controllers.gitlab_controller import (
    sync_repository_admin,
    list_repositories_admin,
    get_repository_sync_history_admin,
    delete_repository_admin,
    test_gitlab_connection_admin,
    SyncRepositoryRequest,
    SyncRepositoryResponse,
    RepositoryListResponse,
    SyncHistoryResponse
)

router = APIRouter()

# Test GitLab connection
router.add_api_route(
    "/test",
    test_gitlab_connection_admin,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Test GitLab connection (Admin)",
    description="Test GitLab API connection using admin token"
)

# Sync repository
router.add_api_route(
    "/sync",
    sync_repository_admin,
    methods=["POST"],
    response_model=SyncRepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync GitLab repository (Admin)",
    description="Sync a GitLab repository and create embeddings"
)

# List repositories
router.add_api_route(
    "/repositories",
    list_repositories_admin,
    methods=["GET"],
    response_model=RepositoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List synced repositories (Admin)",
    description="Get all synced repositories"
)

# Get repository sync history
router.add_api_route(
    "/repositories/{repository_id}/history",
    get_repository_sync_history_admin,
    methods=["GET"],
    response_model=SyncHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get repository sync history (Admin)",
    description="Get sync history for a repository"
)

# Delete repository
router.add_api_route(
    "/repositories/{repository_id}",
    delete_repository_admin,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
    summary="Delete repository (Admin)",
    description="Delete repository and all synced data"
)
