from abc import abstractmethod
from typing import Optional, List
from shared.interfaces.repositories.base_repository import BaseRepository
from domain.entities.user import UserEntity


class UserRepository(BaseRepository[UserEntity, str]):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def find_active_users(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        pass

    @abstractmethod
    async def find_first_admin(self) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def count_active_admins(self, exclude_user_id: Optional[int] = None) -> int:
        pass
