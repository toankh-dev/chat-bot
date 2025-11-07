"""
Group service.

Handles group management business logic.
"""

from typing import List, Optional
from domain.entities.group import Group
from core.errors import NotFoundError, ValidationError
from shared.interfaces.repositories.group_repository import GroupRepository
from shared.interfaces.repositories.user_group_repository import UserGroupRepository


class GroupService:
    """
    Service for group management operations.
    """

    def __init__(
        self,
        group_repository: GroupRepository,
        user_group_repository: Optional[UserGroupRepository] = None
    ):
        self.group_repository = group_repository
        self.user_group_repository = user_group_repository

    async def get_group_member_count(self, group_id: int) -> int:
        """
        Get the number of members in a group.

        Args:
            group_id: Group ID

        Returns:
            int: Number of members in the group
        """
        if not self.user_group_repository:
            return 0

        user_ids = await self.user_group_repository.get_group_users(group_id)
        return len(user_ids)

    async def get_group_by_id(self, group_id: int) -> Group:
        """
        Get group by ID.

        Args:
            group_id: Group ID

        Returns:
            Group: Found group

        Raises:
            NotFoundError: If group not found
        """
        group = await self.group_repository.find_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group with ID {group_id} not found")
        return group

    async def list_groups(self, skip: int = 0, limit: int = 100) -> List[Group]:
        """
        List all groups with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Group]: List of groups
        """
        return await self.group_repository.find_all(skip=skip, limit=limit)

    async def create_group(self, name: str) -> Group:
        """
        Create new group.

        Args:
            name: Group name

        Returns:
            Group: Created group

        Raises:
            ValidationError: If group name already exists
        """
        existing_group = await self.group_repository.find_by_name(name)
        if existing_group:
            raise ValidationError(f"Group with name '{name}' already exists")

        group = Group(name=name)
        return await self.group_repository.create(group)

    async def update_group(
        self,
        group_id: int,
        name: Optional[str] = None
    ) -> Group:
        """
        Update group information.

        Args:
            group_id: Group ID
            name: New name (optional)

        Returns:
            Group: Updated group

        Raises:
            NotFoundError: If group not found
            ValidationError: If new name already exists
        """
        group = await self.get_group_by_id(group_id)

        if name is not None and name != group.name:
            existing_group = await self.group_repository.find_by_name(name)
            if existing_group:
                raise ValidationError(f"Group with name '{name}' already exists")
            group.name = name

        return await self.group_repository.update(group)

    async def delete_group(self, group_id: int) -> bool:
        """
        Delete group.

        Args:
            group_id: Group ID

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If group not found
        """
        if not await self.group_repository.exists(group_id):
            raise NotFoundError(f"Group with ID {group_id} not found")

        return await self.group_repository.delete(group_id)
