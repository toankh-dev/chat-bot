"""GitLab Service Interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IGitLabService(ABC):
    """Interface for GitLab service operations."""

    @abstractmethod
    def get_projects(
        self, owned: bool = False, membership: bool = True, visibility: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of projects from GitLab.

        Args:
            owned: Only owned projects
            membership: Only member projects
            visibility: Filter by visibility (public, internal, private)

        Returns:
            List of project dictionaries
        """
        pass

    @abstractmethod
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """
        Get project information by project path.

        Args:
            project_path: Project path (e.g., "group/project")

        Returns:
            Project information dictionary
        """
        pass

    @abstractmethod
    def get_branches(self, project_id: str) -> List[str]:
        """
        Get all branch names of a GitLab project.

        Args:
            project_id: GitLab project ID or path

        Returns:
            List of branch names
        """
        pass

    @abstractmethod
    def _get_repository_tree(
        self, project_id: str, path: str = "", ref: str = "main", recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get repository tree (file structure).

        Args:
            project_id: GitLab project ID
            path: Path in repository
            ref: Branch/tag name
            recursive: Recursive listing

        Returns:
            List of file/directory dictionaries
        """
        pass

    @abstractmethod
    def get_file_content(self, project_id: str, file_path: str, ref: str = "main") -> bytes:
        """
        Get file content from repository.

        Args:
            project_id: GitLab project ID
            file_path: File path in repository
            ref: Branch/tag name

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    def get_branch_head_commit(self, project_id: str, branch_name: str) -> Dict[str, Any]:
        """
        Get HEAD commit SHA and information of a specific branch.

        Args:
            project_id: Project ID or path
            branch_name: Branch name (e.g., 'main', 'develop')

        Returns:
            Dictionary with HEAD commit information including commit_sha
        """
        pass

    @abstractmethod
    def _extract_project_path(self, repository_url: str) -> str:
        """
        Extract project path from repository URL.

        Args:
            repository_url: Full GitLab repository URL

        Returns:
            Project path (e.g., "group/project")
        """
        pass

    @abstractmethod
    def filter_code_files(self, project_id: str, ref: str = "main", extensions: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> List[str]:
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
        pass
    
    @abstractmethod
    def _list_repositories(self, visibility: Optional[str] = None, owned: bool = False, membership: bool = True, search: Optional[str] = None, order_by: str = "last_activity_at", sort: str = "desc") -> List[Dict[str, Any]]:
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
        pass