"""
Admin controller for connector management.
Provides secure APIs for setting up and managing connectors.
"""

import logging
from typing import List
from fastapi import Depends, HTTPException, status

from core.dependencies import (
    get_list_connectors_use_case,
    get_get_connector_use_case,
    get_setup_gitlab_connector_use_case,
    get_update_connector_credentials_use_case,
    get_delete_connector_use_case
)
from api.middlewares.jwt_middleware import require_admin
from domain.entities.user import UserEntity
from usecases.connector_use_cases import (
    ListConnectorsUseCase,
    GetConnectorUseCase,
    SetupGitLabConnectorUseCase,
    UpdateConnectorCredentialsUseCase,
    DeleteConnectorUseCase
)
from schemas.user_schema import UserResponse
from schemas.connector_schema import (
    ConnectorResponse,
    ConnectorCredentialsUpdateRequest,
    GitLabPersonalTokenSetupRequest,
    MessageResponse
)

logger = logging.getLogger(__name__)


# ============================================================================
# Connector Management Endpoints
# ============================================================================


async def list_connectors(
    use_case: ListConnectorsUseCase = Depends(get_list_connectors_use_case),
    current_user: UserEntity = Depends(require_admin)
) -> List[ConnectorResponse]:
    """
    List all configured connectors.

    Returns:
        List of connector configurations (without sensitive data)
    """
    try:
        connectors = use_case.execute()

        # Convert to response format (excluding sensitive fields)
        return [
            ConnectorResponse(
                id=connector.id,
                name=connector.name,
                provider_type=connector.provider_type,
                auth_type=connector.auth_type,
                is_active=connector.is_active,
                config_schema=connector.config_schema,
                created_at=connector.created_at,
                has_credentials=bool(connector.client_id)
            )
            for connector in connectors
        ]

    except Exception as e:
        logger.error(f"Failed to list connectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connectors: {str(e)}"
        )


async def get_connector(
    connector_id: int,
    use_case: GetConnectorUseCase = Depends(get_get_connector_use_case),
    current_user: UserEntity = Depends(require_admin)
) -> ConnectorResponse:
    """
    Get specific connector configuration.

    Args:
        connector_id: Connector ID to retrieve

    Returns:
        Connector configuration (without sensitive data)
    """
    try:
        connector = use_case.execute(connector_id)

        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=bool(connector.client_id)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get connector {connector_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connector: {str(e)}"
        )


async def setup_gitlab_personal_token_connector(
    request: GitLabPersonalTokenSetupRequest,
    use_case: SetupGitLabConnectorUseCase = Depends(get_setup_gitlab_connector_use_case),
    current_user: UserEntity = Depends(require_admin)
) -> ConnectorResponse:
    """
    Setup GitLab connector with personal access token.
    This endpoint is idempotent - it will update existing connector or create new one.

    Args:
        request: GitLab setup configuration

    Returns:
        Configured connector details (with stable ID)
    """
    try:
        connector = use_case.execute(request)

        logger.info(
            f"Admin {current_user.email} configured GitLab connector: "
            f"ID={connector.id}, URL={request.gitlab_url}"
        )

        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=bool(connector.client_id)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to setup GitLab connector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup GitLab connector: {str(e)}"
        )


async def update_connector_credentials(
    connector_id: int,
    request: ConnectorCredentialsUpdateRequest,
    use_case: UpdateConnectorCredentialsUseCase = Depends(get_update_connector_credentials_use_case),
    current_user: UserEntity = Depends(require_admin)
) -> ConnectorResponse:
    """
    Update connector credentials (personal token).

    Args:
        connector_id: Connector ID to update
        request: New credentials

    Returns:
        Updated connector configuration
    """
    try:
        connector = use_case.execute(connector_id, request)

        logger.info(f"Admin {current_user.email} updated credentials for connector {connector_id}")

        return ConnectorResponse(
            id=connector.id,
            name=connector.name,
            provider_type=connector.provider_type,
            auth_type=connector.auth_type,
            is_active=connector.is_active,
            config_schema=connector.config_schema,
            created_at=connector.created_at,
            has_credentials=bool(connector.client_id)
        )

    except ValueError as e:
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
    use_case: DeleteConnectorUseCase = Depends(get_delete_connector_use_case),
    current_user: UserEntity = Depends(require_admin)
) -> MessageResponse:
    """
    Delete a connector and all its connections.

    Args:
        connector_id: Connector ID to delete

    Returns:
        Success message
    """
    try:
        use_case.execute(connector_id)

        logger.info(f"Admin {current_user.email} deleted connector {connector_id}")

        return MessageResponse(
            message=f"Connector {connector_id} deleted successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete connector: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connector: {str(e)}"
        )
