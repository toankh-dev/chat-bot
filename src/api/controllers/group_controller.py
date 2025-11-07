"""Group management controller."""

from fastapi import Depends
from typing import List
from src.schemas.group_schema import GroupResponse, GroupCreate, GroupUpdate
from src.infrastructure.postgresql.models import User
from src.api.middlewares.jwt_middleware import get_current_user, require_admin
from src.usecases.group_use_cases import (
    ListGroupsUseCase,
    GetGroupUseCase,
    CreateGroupUseCase,
    UpdateGroupUseCase,
    DeleteGroupUseCase
)
from src.core.dependencies import (
    get_list_groups_use_case,
    get_group_use_case,
    get_create_group_use_case,
    get_update_group_use_case,
    get_delete_group_use_case
)


async def list_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    use_case: ListGroupsUseCase = Depends(get_list_groups_use_case)
) -> List[GroupResponse]:
    """
    List all groups.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Authenticated user
        use_case: List groups use case instance

    Returns:
        List[GroupResponse]: List of groups
    """
    return await use_case.execute(skip=skip, limit=limit)


async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    use_case: GetGroupUseCase = Depends(get_group_use_case)
) -> GroupResponse:
    """
    Get group by ID.

    Args:
        group_id: Group ID
        current_user: Authenticated user
        use_case: Get group use case instance

    Returns:
        GroupResponse: Group data
    """
    return await use_case.execute(group_id)


async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(require_admin),
    use_case: CreateGroupUseCase = Depends(get_create_group_use_case)
) -> GroupResponse:
    """
    Create new group (admin only).

    Args:
        group_data: Group creation data
        current_user: Authenticated admin user
        use_case: Create group use case instance

    Returns:
        GroupResponse: Created group data
    """
    return await use_case.execute(group_data)


async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(require_admin),
    use_case: UpdateGroupUseCase = Depends(get_update_group_use_case)
) -> GroupResponse:
    """
    Update group (admin only).

    Args:
        group_id: Group ID
        group_data: Group update data
        current_user: Authenticated admin user
        use_case: Update group use case instance

    Returns:
        GroupResponse: Updated group data
    """
    return await use_case.execute(group_id, group_data)


async def delete_group(
    group_id: int,
    current_user: User = Depends(require_admin),
    use_case: DeleteGroupUseCase = Depends(get_delete_group_use_case)
) -> None:
    """
    Delete group (admin only).

    Args:
        group_id: Group ID
        current_user: Authenticated admin user
        use_case: Delete group use case instance
    """
    await use_case.execute(group_id)
