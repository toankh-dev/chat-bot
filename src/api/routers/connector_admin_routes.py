"""
Connector Admin Routes - Admin connector management endpoints.
Provides secure APIs for setting up and managing connectors.
"""

from typing import List, Dict
from fastapi import APIRouter, Depends
from api.middlewares.jwt_middleware import require_admin
from api.controllers.connector_admin_controller import (
    list_connectors,
    get_connector,
    setup_gitlab_personal_token_connector,
    update_connector_credentials,
    delete_connector
)
from schemas.connector_schema import ConnectorResponse

router = APIRouter(dependencies=[Depends(require_admin)])

# Register all connector admin endpoints
router.add_api_route(
    "/",
    list_connectors,
    methods=["GET"],
    response_model=List[ConnectorResponse],
    summary="List Connectors",
    description="Get all configured connectors (admin only)"
)

router.add_api_route(
    "/{connector_id}",
    get_connector,
    methods=["GET"],
    response_model=ConnectorResponse,
    summary="Get Connector",
    description="Get connector details by ID (admin only)"
)

router.add_api_route(
    "/gitlab/token",
    setup_gitlab_personal_token_connector,
    methods=["POST"],
    response_model=ConnectorResponse,
    summary="Setup GitLab Personal Token",
    description="Setup GitLab connector with personal access token (admin only)"
)

router.add_api_route(
    "/{connector_id}/credentials",
    update_connector_credentials,
    methods=["PUT"],
    response_model=ConnectorResponse,
    summary="Update Connector Credentials",
    description="Update connector personal token credentials (admin only)"
)

router.add_api_route(
    "/{connector_id}",
    delete_connector,
    methods=["DELETE"],
    response_model=Dict[str, str],
    summary="Delete Connector",
    description="Delete a connector and all its connections (admin only)"
)