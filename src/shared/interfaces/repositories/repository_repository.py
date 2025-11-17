"""Repository Repository Interface for managing git repositories."""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime


class IRepositoryRepository(ABC):
    """Interface for repository repository operations."""

    @abstractmethod
    def create(self, repository):
        pass

    @abstractmethod
    def get_by_id(self, repo_id: int):
        pass

    @abstractmethod
    def get_or_create(self, connection_id: int, external_id: str, defaults: dict = None):
        pass

    @abstractmethod
    def get_by_connection_and_external_id(self, connection_id: int, external_id: str):
        pass

    @abstractmethod
    def list_by_connection(self, connection_id: int, only_active: bool = True):
        pass

    @abstractmethod
    def list_user_repositories(self, user_id: int):
        pass

    @abstractmethod
    def update(self, repository):
        pass

    @abstractmethod
    def update_sync_status(self, repo_id: int, status: str, last_synced_at = None):
        pass

    @abstractmethod
    def mark_syncing(self, repo_id: int):
        pass

    @abstractmethod
    def mark_completed(self, repo_id: int, last_synced_at = None):
        pass

    @abstractmethod
    def mark_failed(self, repo_id: int):
        pass

    @abstractmethod
    def delete(self, repo_id: int) -> bool:
        pass

    @abstractmethod
    def deactivate(self, repo_id: int):
        pass

    @abstractmethod
    def get_pending_sync_repositories(self):
        pass

    @abstractmethod
    def get_stale_syncing_repositories(self, stale_minutes: int = 60):
        pass
