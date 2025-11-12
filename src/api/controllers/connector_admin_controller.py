"""
Admin controller for connector management.
Provides secure APIs for setting up and managing connectors.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status

from core.dependencies import get_current_admin_user, get_connector_use_cases
from usecases.connector_use_cases import ConnectorUseCases
from schemas.user_schema import UserResponse
from schemas.connector_schema import (
    ConnectorCreateRequest, ConnectorResponse, ConnectorCredentialsUpdateRequest,
    GitLabPersonalTokenSetupRequest
)

logger = logging.getLogger(__name__)


# ============================================================================
# Connector Management Endpoints
# ============================================================================


async def list_connectors(
    connector_use_cases: ConnectorUseCases = Depends(get_connector_use_cases),
    current_user: UserResponse = Depends(get_current_admin_user)
) -> List[ConnectorResponse]:
    """
    List all configured connectors.
    
    Returns:
        List of connector configurations (without sensitive data)
    """
    try:
        connectors = connector_use_cases.list_connectors()
        
        # Convert to response format (excluding sensitive fields)
        connector_responses = []
        for connector in connectors:
            connector_responses.append(ConnectorResponse(
                id=connector.id,
                name=connector.name,
                provider_type=connector.provider_type,
                auth_type=connector.auth_type,
                is_active=connector.is_active,
                config_schema=connector.config_schema,
                created_at=connector.created_at,
                has_credentials=bool(connector.client_id)  # Personal token stored in client_id
            ))
        
        return connector_responses
        
    except Exception as e:
        logger.error(f"Failed to list connectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connectors: {str(e)}"
        )


async def get_connector(
    connector_id: int,
    connector_use_cases: ConnectorUseCases = Depends(get_connector_use_cases),
    current_user: UserResponse = Depends(get_current_admin_user)
) -> ConnectorResponse:
    """
    Get specific connector configuration.
    
    Args:
        connector_id: Connector ID to retrieve
        
    Returns:
        Connector configuration (without sensitive data)
    """
    try:
        connector = connector_use_cases.get_connector_by_id(connector_id)
        
        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=bool(connector.client_id)  # Personal token stored in client_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connector {connector_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connector: {str(e)}"
        )


async def setup_gitlab_personal_token_connector(
    request: GitLabPersonalTokenSetupRequest,
    connector_use_cases: ConnectorUseCases = Depends(get_connector_use_cases),
    current_user: UserResponse = Depends(get_current_admin_user)
) -> ConnectorResponse:
    """
    Setup GitLab connector with personal access token.

    Args:
        request: GitLab personal token setup configuration

    Returns:
        Created connector configuration
    """
    try:
        connector = connector_use_cases.setup_gitlab_personal_token_connector(request)
        
        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=bool(request.admin_token)
        )
        
    except ValueError as e:
        logger.warning(f"GitLab token setup validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to setup GitLab token connector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup GitLab token connector: {str(e)}"
        )


async def update_connector_credentials(
    connector_id: int,
    request: ConnectorCredentialsUpdateRequest,
    connector_use_cases: ConnectorUseCases = Depends(get_connector_use_cases),
    current_user: UserResponse = Depends(get_current_admin_user)
) -> ConnectorResponse:
    """
    Update connector credentials.

    Args:
        connector_id: Connector ID to update
        request: New credentials

    Returns:
        Updated connector configuration
    """
    try:
        connector = connector_use_cases.update_connector_credentials(connector_id, request)
        
        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=True
        )
        
    except ValueError as e:
        logger.warning(f"Credentials update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update connector credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update credentials: {str(e)}"
        )


async def delete_connector(
    connector_id: int,
    connector_use_cases: ConnectorUseCases = Depends(get_connector_use_cases),
    current_user: UserResponse = Depends(get_current_admin_user)
) -> Dict[str, str]:
    """
    Delete a connector and all its connections.

    Args:
        connector_id: Connector ID to delete

    Returns:
        Success message
    """
    try:
        connector_use_cases.delete_connector(connector_id)
        
        return {"message": f"Connector {connector_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete connector {connector_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connector: {str(e)}"
        )