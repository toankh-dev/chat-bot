"""
GitLab Service - Interface with GitLab API for repository operations.
"""

import gitlab
import base64
from typing import Dict, List, Any, Optional
from core.logger import logger

from shared.interfaces.services.external.gitlab_service import IGitLabService
from core.errors import (
    GitLabAuthenticationError,
    GitLabNetworkError,
    GitLabError,
    GitLabAPIError,
    GitLabRateLimitError,
    RepositoryBranchNotFoundError
)
class GitLabService(IGitLabService):
    """Service for interacting with GitLab repositories."""

    def __init__(self, gitlab_url: str, private_token: str):
        """
        Initialize GitLab service.

        Args:
            gitlab_url: GitLab instance URL (e.g., https://gitlab.com)
            private_token: GitLab personal access token
        """
        self.gitlab_url = gitlab_url
        self.private_token = private_token
        self.gl = gitlab.Gitlab(gitlab_url, private_token=private_token)

        # Authenticate
        try:
            self.gl.auth()
            logger.info(
                "GitLab authentication successful",
                extra={"username": self.gl.user.username, "gitlab_url": gitlab_url}
            )
        except gitlab.exceptions.GitlabAuthenticationError as e:
            logger.error("GitLab authentication failed: Invalid token or credentials")
            raise GitLabAuthenticationError(
                "Authentication failed. Please check your GitLab token."
            ) from e
        except gitlab.exceptions.GitlabHttpError as e:
            logger.error(f"GitLab HTTP error during authentication: {e}")
            raise GitLabNetworkError(
                gitlab_url=gitlab_url,
                message="Cannot connect to GitLab"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during GitLab authentication: {e}")
            raise GitLabError(message=f"Authentication failed: {e}") from e

    def get_file_content(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> str:
        """
        Get content of a specific file.

        Args:
            project_id: Project ID or path
            file_path: Path to file within repository
            ref: Branch/tag/commit reference

        Returns:
            File content as string
        """
        try:
            project = self.gl.projects.get(project_id)
            file_info = project.files.get(file_path=file_path, ref=ref)

            # Decode base64 content
            content = base64.b64decode(file_info.content).decode('utf-8')

            return content
        except Exception as e:
            raise ValueError(f"Failed to get file content: {str(e)}")

    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information.

        Args:
            project_id: Project ID or path

        Returns:
            Dictionary with project information
        """
        try:
            project = self.gl.projects.get(project_id)

            return {
                "id": project.id,
                "name": project.name,
                "path": project.path,
                "path_with_namespace": project.path_with_namespace,
                "description": project.description,
                "web_url": project.web_url,
                "default_branch": project.default_branch,
                "created_at": project.created_at,
                "last_activity_at": project.last_activity_at
            }
        except Exception as e:
            raise ValueError(f"Failed to get project info: {str(e)}")

    def get_branches(self, project_id: str) -> List[str]:
        """
        Get all branch names of a GitLab project.

        Args:
            project_id: GitLab project ID or path

        Returns:
            List of branch names
        """
        try:
            project = self.gl.projects.get(project_id)
            branches = project.branches.list()

            # Return only branch names
            return [branch.name for branch in branches]

        except Exception as e:
            raise ValueError(f"Failed to get branches for project {project_id}: {str(e)}")

    def get_branch_head_commit(
        self,
        project_id: str,
        branch_name: str
    ) -> Dict[str, Any]:
        """
        Get HEAD commit SHA and information of a specific branch.

        Args:
            project_id: Project ID or path
            branch_name: Branch name (e.g., 'main', 'develop')

        Returns:
            Dictionary with HEAD commit information:
            {
                "branch_name": str,
                "commit_sha": str,
                "short_sha": str,
                "author_name": str,
                "author_email": str,
                "committed_at": str,
                "message": str,
                "title": str
            }

        Raises:
            ValueError: If branch not found or API call fails
        """
        try:
            project = self.gl.projects.get(project_id)
            branch = project.branches.get(branch_name)
            return {
                "branch_name": branch_name,
                "commit_sha": branch.commit["id"],
                "short_sha": branch.commit["short_id"],
                "author_name": branch.commit["author_name"],
                "author_email": branch.commit["author_email"],
                "committed_at": branch.commit["committed_date"],
                "message": branch.commit["message"],
                "title": branch.commit["title"]
            }
        except Exception as e:
            raise ValueError(f"Failed to get HEAD commit for branch '{branch_name}': {str(e)}")

    def filter_code_files(
        self,
        project_id: str,
        ref: str = "main",
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filter code files from file list.

        Args:
            project_id: Project ID or path
            ref: Branch/tag/commit reference
            file_list: List of file paths
            extensions: List of file extensions to include (e.g., ['.py', '.js'])
            exclude_patterns: List of patterns to exclude (e.g., ['test_', '__pycache__'])

        Returns:
            Filtered list of code files
        """
        tree = self._get_repository_tree(
            project_id=project_id, ref=ref, recursive=True
        )

        # Filter code files
        if not isinstance(tree, list):
            raise GitLabAPIError("Unexpected response format from GitLab API: expected list")
        
        file_paths = [item.get("path") for item in tree if item.get("type") == "blob" and item.get("path")]
        # Default code file extensions
        if extensions is None:
            extensions = [
                ".py", ".js", ".ts", ".tsx", ".jsx",
                ".java", ".go", ".rs", ".cpp", ".c", ".h",
                ".rb", ".php", ".swift", ".kt", ".scala",
                ".cs", ".sql", ".sh", ".yaml", ".yml",
                ".json", ".xml", ".md"
            ]

        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = [
                "node_modules/",
                "__pycache__/",
                ".git/",
                "dist/",
                "build/",
                "target/",
                ".pytest_cache/",
                "coverage/",
                ".venv/",
                "venv/",
                "test_",
                "_test.",
                ".test.",
                ".min.js",
                ".min.css"
            ]

        filtered_files = []

        for file_path in file_paths:
            # Check extension
            has_valid_extension = any(file_path.endswith(ext) for ext in extensions)

            if not has_valid_extension:
                continue

            # Check exclude patterns
            should_exclude = any(pattern in file_path for pattern in exclude_patterns)

            if should_exclude:
                continue

            filtered_files.append(file_path)

        return filtered_files

    def get_projects(
        self,
        owned: bool = False,
        membership: bool = True,
        visibility: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get projects (alias for list_repositories with pagination info).

        Args:
            owned: Only owned projects
            membership: Only member projects
            visibility: Filter by visibility (public, internal, private)
            **kwargs: Additional parameters for list_repositories

        Returns:
            Dictionary with repositories and pagination info
        """
        repositories = self._list_repositories(
            owned=owned,
            membership=membership,
            visibility=visibility,
            **kwargs
        )

        # Always return all repositories with single page info
        return {
            "repositories": repositories,
            "total": len(repositories),
        }

    def _extract_project_path(self, repo_url: str) -> str:
        """
        Extract project path from repository URL.

        Args:
            repo_url: Repository URL

        Returns:
            Project path (e.g., "user/project")
        """
        # Remove protocol and domain
        path = repo_url.replace("https://", "").replace("http://", "")

        # Remove gitlab.com or custom domain
        parts = path.split("/")
        if len(parts) >= 3:
            # Format: domain/user/project or domain/group/subgroup/project
            return "/".join(parts[1:])

        raise ValueError(f"Invalid repository URL: {repo_url}")

    def _get_repository_tree(
        self,
        project_id: str,
        ref: str = "main",
        path: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get repository file tree.

        Args:
            project_id: Project ID or path
            ref: Branch/tag/commit reference
            path: Directory path within repository
            recursive: Whether to get tree recursively

        Returns:
            List of file/directory information
        """
        try:
            project = self.gl.projects.get(project_id)

            tree = project.repository_tree(
                ref=ref,
                path=path,
                recursive=recursive,
                all=True
            )

            return [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["type"],
                    "path": item["path"],
                    "mode": item["mode"]
                }
                for item in tree
            ]

        except gitlab.exceptions.GitlabGetError as e:
            if e.response_code == 404:
                raise RepositoryBranchNotFoundError(
                    repo_id=project_id,
                    branch=ref
                ) from e
            elif e.response_code == 429:
                retry_after = e.response_headers.get('Retry-After', 60) if hasattr(e, 'response_headers') else 60
                raise GitLabRateLimitError(retry_after=int(retry_after)) from e
            else:
                raise GitLabAPIError(
                    message=f"Failed to fetch repository tree: {str(e)}",
                    status_code=e.response_code
                ) from e
        except Exception as e:
            raise GitLabAPIError(message=f"Unexpected error fetching repository tree: {str(e)}") from e
        
    def _list_repositories(
        self,
        visibility: Optional[str] = None,
        owned: bool = False,
        membership: bool = True,
        search: Optional[str] = None,
        order_by: str = "last_activity_at",
        sort: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        List GitLab repositories accessible to the authenticated user.

        Args:
            visibility: Filter by visibility (public, internal, private)
            owned: Limit to owned projects only
            membership: Limit to projects user is a member of
            search: Search term to filter repositories by name/description
            order_by: Sort by field (id, name, path, created_at, updated_at, last_activity_at)
            sort: Sort order (asc or desc)

        Returns:
            List of repository information dictionaries
        """
        try:
            # Always fetch all repositories without pagination
            all_repositories = []
            current_page = 1
            per_page_batch = 100  # GitLab max per page

            while True:
                # Build query parameters for current batch
                list_params = {
                    "order_by": order_by,
                    "sort": sort,
                    "per_page": per_page_batch,
                    "page": current_page
                }

                if visibility:
                    list_params["visibility"] = visibility
                if owned:
                    list_params["owned"] = True
                if membership:
                    list_params["membership"] = True
                if search:
                    list_params["search"] = search

                # Get projects from GitLab API
                projects = self.gl.projects.list(**list_params)

                if not projects:
                    break

                # Transform to simplified format and add to results
                for project in projects:
                    all_repositories.append({
                        "id": str(project.id),
                        "external_id": str(project.id),
                        "name": project.name,
                        "path": project.path,
                        "full_name": project.path_with_namespace,
                        "description": project.description or "",
                        "visibility": project.visibility,
                        "web_url": project.web_url,
                        "http_url_to_repo": project.http_url_to_repo,
                        "default_branch": project.default_branch or "main",
                        "created_at": project.created_at,
                        "last_activity_at": project.last_activity_at,
                        "star_count": getattr(project, "star_count", 0),
                        "forks_count": getattr(project, "forks_count", 0),
                        "archived": getattr(project, "archived", False),
                        "empty_repo": getattr(project, "empty_repo", False)
                    })

                # If we got less than per_page_batch, we've reached the end
                if len(projects) < per_page_batch:
                    break

                current_page += 1

            return all_repositories

        except Exception as e:
            raise ValueError(f"Failed to list repositories: {str(e)}")