"""
PostgreSQL implementation of IngestionJobRepository.
"""
from typing import List, Optional
from src.domain.entities.ingestion_job import IngestionJob
from src.shared.repositories.ingestion_job_repository import IngestionJobRepository

class IngestionJobRepository(IngestionJobRepository):
    def __init__(self, session):
        self.session = session

    async def create(self, job: IngestionJob) -> IngestionJob:
        # Implement SQLAlchemy insert logic here
        pass

    async def find_by_id(self, id: int) -> Optional[IngestionJob]:
        # Implement SQLAlchemy select by id
        pass

    async def find_by_user(self, user_id: int) -> List[IngestionJob]:
        # Implement SQLAlchemy select by user_id
        pass

    async def update_status(self, id: int, status: str, error_message: str = None) -> bool:
        # Implement SQLAlchemy update status
        pass

    async def delete(self, id: int) -> bool:
        # Implement SQLAlchemy delete by id
        pass
