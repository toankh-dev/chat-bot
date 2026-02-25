"""
AI Model repository interface.

Defines the contract for AI model data access operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.ai_model import AiModelEntity


class AiModelRepository(BaseRepository[AiModelEntity, int], ABC):
    """
    AI Model repository interface.

    Extends BaseRepository with AI model-specific operations.
    """

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[AiModelEntity]:
        """
        Find AI model by name.

        Args:
            name: Model name

        Returns:
            AiModel if found, None otherwise
        """
        pass

