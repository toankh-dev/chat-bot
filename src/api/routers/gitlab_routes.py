"""
GitLab Routes - Admin-only repository sync (simplified).
"""

from fastapi import APIRouter, status

from api.controllers.gitlab_controller import (
    sync_repository_admin,
    test_gitlab_connection_admin,
    fetch_gitlab_repositories_admin
)
from schemas.gitlab_schema import (
    SyncRepositoryRequest,
    SyncRepositoryResponse,
    GitLabRepositoryListResponse
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

# Fetch repositories from GitLab
router.add_api_route(
    "/fetch-repositories",
    fetch_gitlab_repositories_admin,
    methods=["GET"],
    response_model=GitLabRepositoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch GitLab repositories (Admin)",
    description="Fetch all accessible repositories from GitLab API using a specific connector without pagination (does not save to database)"
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
