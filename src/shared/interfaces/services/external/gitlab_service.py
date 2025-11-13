"""GitLab Service Interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IGitLabService(ABC):
    """Interface for GitLab service operations."""

    @abstractmethod
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.

        Returns:
            User information dictionary
        """
        pass

    @abstractmethod
    def get_projects(
        self,
        owned: bool = False,
        membership: bool = True,
        visibility: Optional[str] = None
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
    def get_repository_tree(
        self,
        project_id: str,
        path: str = "",
        ref: str = "main",
        recursive: bool = False
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
    def get_file_content(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main"
    ) -> bytes:
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
    def _extract_project_path(self, repository_url: str) -> str:
        """
        Extract project path from repository URL.

        Args:
            repository_url: Full GitLab repository URL

        Returns:
            Project path (e.g., "group/project")
        """
        pass
