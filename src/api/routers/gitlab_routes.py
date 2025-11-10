"""GitLab integration routes."""

from fastapi import APIRouter, status
from api.controllers.gitlab_controller import (
    sync_repository,
    list_repositories,
    get_sync_status,
    delete_repository_sync,
    test_gitlab_connection,
    SyncRepositoryResponse,
    SyncStatusResponse
)

router = APIRouter()

router.add_api_route(
    "/sync",
    sync_repository,
    methods=["POST"],
    response_model=SyncRepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync GitLab repository",
    description="Sync a GitLab repository to Knowledge Base"
)

router.add_api_route(
    "/repos",
    list_repositories,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="List synced repositories",
    description="List all synced repositories for a group"
)

router.add_api_route(
    "/status/{group_id}",
    get_sync_status,
    methods=["GET"],
    response_model=SyncStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sync status",
    description="Get sync status for repositories in a group"
)

router.add_api_route(
    "/repos/{group_id}",
    delete_repository_sync,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
    summary="Delete repository sync",
    description="Delete all documents synced from a specific repository"
)

router.add_api_route(
    "/test",
    test_gitlab_connection,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    summary="Test GitLab connection",
    description="Test GitLab API connection"
)
