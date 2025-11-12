"""
GitLab Service - Interface with GitLab API for repository operations.
"""

from typing import Dict, List, Any, Optional
import gitlab
import os
import tempfile
import shutil
from pathlib import Path


class GitLabService:
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
            print(f"✅ GitLab authentication successful: {self.gl.user.username}")
        except Exception as e:
            print(f"❌ GitLab authentication failed: {e}")
            raise

    def clone_repository(
        self,
        repo_url: str,
        branch: str = "main",
        target_path: Optional[str] = None
    ) -> str:
        """
        Clone a GitLab repository to local directory.

        Args:
            repo_url: Repository URL (e.g., https://gitlab.com/user/project)
            branch: Branch name to clone
            target_path: Target directory path (optional, uses temp dir if not provided)

        Returns:
            Path to cloned repository

        Raises:
            ValueError: If repository cannot be cloned
        """
        try:
            # Create temp directory if target not specified
            if target_path is None:
                target_path = tempfile.mkdtemp(prefix="gitlab_clone_")
            else:
                os.makedirs(target_path, exist_ok=True)

            # Extract project path from URL
            project_path = self._extract_project_path(repo_url)

            # Get project
            project = self.gl.projects.get(project_path)

            # Clone using git command (requires git installed)
            clone_url = project.http_url_to_repo

            # Add token to URL for authentication
            authenticated_url = clone_url.replace(
                "https://",
                f"https://oauth2:{self.private_token}@"
            )

            import subprocess
            result = subprocess.run(
                ["git", "clone", "-b", branch, authenticated_url, target_path],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise ValueError(f"Git clone failed: {result.stderr}")

            print(f"✅ Repository cloned to: {target_path}")
            return target_path

        except Exception as e:
            if target_path and os.path.exists(target_path):
                shutil.rmtree(target_path)
            raise ValueError(f"Failed to clone repository: {str(e)}")

    def get_repository_tree(
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

        except Exception as e:
            raise ValueError(f"Failed to get repository tree: {str(e)}")

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
            import base64
            content = base64.b64decode(file_info.content).decode('utf-8')

            return content

        except Exception as e:
            raise ValueError(f"Failed to get file content: {str(e)}")

    def list_repositories(
        self,
        visibility: Optional[str] = None,
        owned: bool = False,
        membership: bool = True,
        search: Optional[str] = None,
        order_by: str = "last_activity_at",
        sort: str = "desc",
        per_page: int = 100,
        page: int = 1
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
            per_page: Number of results per page (max 100)
            page: Page number

        Returns:
            List of repository information dictionaries
        """
        try:
            # Build query parameters
            list_params = {
                "order_by": order_by,
                "sort": sort,
                "per_page": min(per_page, 100),  # GitLab max is 100
                "page": page
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

            # Transform to simplified format
            repositories = []
            for project in projects:
                repositories.append({
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

            return repositories

        except Exception as e:
            raise ValueError(f"Failed to list repositories: {str(e)}")

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

    def get_commit_info(
        self,
        project_id: str,
        commit_sha: str
    ) -> Dict[str, Any]:
        """
        Get commit information.

        Args:
            project_id: Project ID or path
            commit_sha: Commit SHA

        Returns:
            Dictionary with commit information
        """
        try:
            project = self.gl.projects.get(project_id)
            commit = project.commits.get(commit_sha)

            return {
                "id": commit.id,
                "short_id": commit.short_id,
                "title": commit.title,
                "message": commit.message,
                "author_name": commit.author_name,
                "author_email": commit.author_email,
                "created_at": commit.created_at,
                "web_url": commit.web_url
            }

        except Exception as e:
            raise ValueError(f"Failed to get commit info: {str(e)}")

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

    def filter_code_files(
        self,
        file_list: List[str],
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filter code files from file list.

        Args:
            file_list: List of file paths
            extensions: List of file extensions to include (e.g., ['.py', '.js'])
            exclude_patterns: List of patterns to exclude (e.g., ['test_', '__pycache__'])

        Returns:
            Filtered list of code files
        """
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

        for file_path in file_list:
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

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.

        Returns:
            Dictionary with user information
        """
        try:
            user = self.gl.user
            return {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "email": getattr(user, 'email', ''),
                "avatar_url": getattr(user, 'avatar_url', ''),
                "web_url": getattr(user, 'web_url', '')
            }
        except Exception as e:
            raise ValueError(f"Failed to get current user: {str(e)}")

    def get_projects(
        self,
        per_page: int = 20,
        page: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get projects (alias for list_repositories with pagination info).

        Args:
            per_page: Number of projects per page
            page: Page number
            **kwargs: Additional parameters for list_repositories

        Returns:
            Dictionary with repositories and pagination info
        """
        repositories = self.list_repositories(
            per_page=per_page,
            page=page,
            **kwargs
        )

        return {
            "repositories": repositories,
            "total": len(repositories),
            "page": page,
            "per_page": per_page
        }

    def cleanup_clone(self, clone_path: str):
        """
        Clean up cloned repository.

        Args:
            clone_path: Path to cloned repository
        """
        try:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
                print(f"✅ Cleaned up: {clone_path}")
        except Exception as e:
            print(f"⚠️ Failed to cleanup {clone_path}: {e}")
