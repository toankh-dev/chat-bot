"""
GitLab API schema definitions.

This module contains all request and response schemas for GitLab operations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# GitLab Request Schemas
# ============================================================================

class SyncRepositoryRequest(BaseModel):
    """Request model for syncing a repository."""
    repository_url: str = Field(..., description="GitLab repository URL (e.g., https://gitlab.com/group/project)")
    chatbot_id: int = Field(..., description="Chatbot ID to link this repository to")
    branch: Optional[str] = Field(default=None, description="Branch to sync (uses default branch if not specified)")
    auto_sync: bool = Field(default=False, description="Auto-sync on GitLab webhook events")


# ============================================================================
# GitLab Response Schemas
# ============================================================================

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

class GitLabConnectionTestResponse(BaseModel):
    """Response for GitLab connection test."""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None


class GitLabBranchListResponse(BaseModel):
    """Response for fetching GitLab branches."""
    branches: List[str]  # Simple list of branch names