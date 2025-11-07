"""
AWS Lambda handler for WebSocket API Gateway.

Handles WebSocket connection lifecycle and message routing.
"""

import json
from typing import Dict, Any
from core.logger import logger
from core.config import settings


async def connect_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $connect route.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    connection_id = event['requestContext']['connectionId']
    logger.info(f"WebSocket connection request: {connection_id}")

    try:
        # Extract and validate JWT from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        token = query_params.get('token')

        if not token:
            logger.warning(f"Connection {connection_id} rejected: No token provided")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }

        # Validate token (implement JWT validation)
        # from infrastructure.auth.jwt_handler import get_jwt_handler
        # jwt_handler = get_jwt_handler()
        # user_id = jwt_handler.get_token_subject(token)

        # await store_connection(connection_id, user_id)

        logger.info(f"WebSocket connection established: {connection_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected'})
        }

    except Exception as e:
        logger.error(f"Connection error for {connection_id}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


async def disconnect_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $disconnect route.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    connection_id = event['requestContext']['connectionId']
    logger.info(f"WebSocket disconnect request: {connection_id}")

    try:
        # await remove_connection(connection_id)

        logger.info(f"WebSocket connection closed: {connection_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected'})
        }

    except Exception as e:
        logger.error(f"Disconnect error for {connection_id}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


async def message_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket messages.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    connection_id = event['requestContext']['connectionId']
    logger.info(f"WebSocket message from: {connection_id}")

    try:
        body = json.loads(event.get('body', '{}'))
        message_type = body.get('type')
        content = body.get('content')

        logger.info(f"Message type: {message_type}, connection: {connection_id}")

        # Route message based on type
        if message_type == 'chat':
            # Handle chat message
            # response = await process_chat_message(connection_id, content)
            response = {"message": "Chat processing not yet implemented"}
        elif message_type == 'typing':
            # Handle typing indicator
            response = {"message": "Typing indicator received"}
        else:
            response = {"error": f"Unknown message type: {message_type}"}

        # Send response back through WebSocket
        # await send_websocket_message(connection_id, response)

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    except Exception as e:
        logger.error(f"Message handling error for {connection_id}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes WebSocket events.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    route_key = event['requestContext']['routeKey']
    logger.info(f"WebSocket route: {route_key}")

    import asyncio

    if route_key == '$connect':
        return asyncio.run(connect_handler(event, context))
    elif route_key == '$disconnect':
        return asyncio.run(disconnect_handler(event, context))
    elif route_key == '$default' or route_key == 'message':
        return asyncio.run(message_handler(event, context))
    else:
        logger.warning(f"Unknown route: {route_key}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unknown route'})
        }
