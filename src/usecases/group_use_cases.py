"""
Group use cases.

Defines application-level use cases for group operations.
"""

from typing import List
from src.application.services.group_service import GroupService
from src.schemas.group_schema import (
    GroupCreate,
    GroupUpdate,
    GroupResponse
)


class ListGroupsUseCase:
    """
    Use case for listing groups.
    """

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    async def execute(self, skip: int = 0, limit: int = 100) -> List[GroupResponse]:
        """
        Execute list groups use case.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[GroupResponse]: List of groups with member counts
        """
        groups = await self.group_service.list_groups(skip=skip, limit=limit)

        # Build responses with member counts
        responses = []
        for group in groups:
            member_count = await self.group_service.get_group_member_count(group.id)
            group_dict = {
                "id": group.id,
                "name": group.name,
                "created_at": group.created_at,
                "updated_at": group.updated_at,
                "member_count": member_count
            }
            responses.append(GroupResponse.model_validate(group_dict))

        return responses


class GetGroupUseCase:
    """
    Use case for getting group by ID.
    """

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    async def execute(self, group_id: int) -> GroupResponse:
        """
        Execute get group use case.

        Args:
            group_id: Group ID

        Returns:
            GroupResponse: Group data with member count
        """
        group = await self.group_service.get_group_by_id(group_id)
        member_count = await self.group_service.get_group_member_count(group_id)

        group_dict = {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "member_count": member_count
        }
        return GroupResponse.model_validate(group_dict)


class CreateGroupUseCase:
    """
    Use case for creating group.
    """

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    async def execute(self, request: GroupCreate) -> GroupResponse:
        """
        Execute create group use case.

        Args:
            request: Group creation data

        Returns:
            GroupResponse: Created group data
        """
        group = await self.group_service.create_group(name=request.name)
        member_count = await self.group_service.get_group_member_count(group.id)

        group_dict = {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "member_count": member_count
        }
        return GroupResponse.model_validate(group_dict)


class UpdateGroupUseCase:
    """
    Use case for updating group.
    """

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    async def execute(self, group_id: int, request: GroupUpdate) -> GroupResponse:
        """
        Execute update group use case.

        Args:
            group_id: Group ID
            request: Group update data

        Returns:
            GroupResponse: Updated group data
        """
        group = await self.group_service.update_group(
            group_id=group_id,
            name=request.name
        )
        member_count = await self.group_service.get_group_member_count(group_id)

        group_dict = {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "member_count": member_count
        }
        return GroupResponse.model_validate(group_dict)


class DeleteGroupUseCase:
    """
    Use case for deleting group.
    """

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    async def execute(self, group_id: int) -> bool:
        """
        Execute delete group use case.

        Args:
            group_id: Group ID

        Returns:
            bool: True if deleted
        """
        return await self.group_service.delete_group(group_id)
