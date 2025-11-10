"""
GitLab Service - Interface with GitLab API for repository operations.
"""

from typing import Dict, List, Any, Optional
import gitlab
import os
import tempfile
import shutil
from pathlib import Path
import hashlib
import hmac


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

    def validate_webhook_signature(
        self,
        secret: str,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate GitLab webhook signature.

        Args:
            secret: Webhook secret token
            payload: Request payload (bytes)
            signature: X-Gitlab-Token header value

        Returns:
            True if signature is valid, False otherwise
        """
        # GitLab uses simple token comparison (not HMAC like GitHub)
        return signature == secret

    def parse_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse GitLab push event payload.

        Args:
            payload: Push event payload from webhook

        Returns:
            Dictionary with parsed event information
        """
        try:
            return {
                "event_type": "push",
                "repository": {
                    "name": payload["project"]["name"],
                    "path": payload["project"]["path_with_namespace"],
                    "url": payload["project"]["web_url"],
                    "id": payload["project"]["id"]
                },
                "ref": payload["ref"],
                "branch": payload["ref"].replace("refs/heads/", ""),
                "before": payload["before"],
                "after": payload["after"],
                "commits": [
                    {
                        "id": commit["id"],
                        "message": commit["message"],
                        "author": {
                            "name": commit["author"]["name"],
                            "email": commit["author"]["email"]
                        },
                        "timestamp": commit["timestamp"],
                        "added": commit.get("added", []),
                        "modified": commit.get("modified", []),
                        "removed": commit.get("removed", [])
                    }
                    for commit in payload["commits"]
                ],
                "user": {
                    "name": payload["user_name"],
                    "email": payload["user_email"],
                    "username": payload["user_username"]
                }
            }

        except KeyError as e:
            raise ValueError(f"Invalid push event payload: missing key {e}")

    def get_changed_files(self, parsed_event: Dict[str, Any]) -> List[str]:
        """
        Extract list of changed files from push event.

        Args:
            parsed_event: Parsed push event from parse_push_event()

        Returns:
            List of file paths that were changed
        """
        changed_files = set()

        for commit in parsed_event["commits"]:
            changed_files.update(commit.get("added", []))
            changed_files.update(commit.get("modified", []))
            # Note: We might want to handle removed files differently

        return list(changed_files)

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
