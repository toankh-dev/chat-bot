"""Group routes."""

from fastapi import APIRouter, status
from typing import List
from src.api.controllers.group_controller import (
    list_groups,
    get_group,
    create_group,
    update_group,
    delete_group
)
from src.schemas.group_schema import GroupResponse

router = APIRouter()

router.add_api_route(
    "/",
    list_groups,
    methods=["GET"],
    response_model=List[GroupResponse],
    status_code=status.HTTP_200_OK,
    summary="List groups",
    description="List all groups"
)

router.add_api_route(
    "/{group_id}",
    get_group,
    methods=["GET"],
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get group by ID",
    description="Get group details by ID"
)

router.add_api_route(
    "/",
    create_group,
    methods=["POST"],
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create group",
    description="Create new group (admin only)"
)

router.add_api_route(
    "/{group_id}",
    update_group,
    methods=["PATCH"],
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Update group",
    description="Update group information (admin only)"
)

router.add_api_route(
    "/{group_id}",
    delete_group,
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete group",
    description="Delete group (admin only)"
)
