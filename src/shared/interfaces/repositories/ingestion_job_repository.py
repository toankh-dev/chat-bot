"""
IngestionJob repository interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.ingestion_job import IngestionJob

class IngestionJobRepository(ABC):
    @abstractmethod
    async def create(self, job: IngestionJob) -> IngestionJob:
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[IngestionJob]:
        pass

    @abstractmethod
    async def find_by_user(self, user_id: int) -> List[IngestionJob]:
        pass

    @abstractmethod
    async def update_status(self, id: int, status: str, error_message: str = None) -> bool:
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
