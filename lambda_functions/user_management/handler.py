"""
User Management Lambda Handler
Uses Mangum to adapt FastAPI for AWS Lambda and API Gateway
"""

from mangum import Mangum
from app import app

# Create Lambda handler using Mangum adapter
# Mangum automatically handles API Gateway proxy integration
handler = Mangum(app, lifespan="off")

# For AWS Lambda, the handler function must be named 'lambda_handler' or 'handler'
lambda_handler = handler


# Optional: Custom handler wrapper for additional functionality
def handler_with_logging(event, context):
    """
    Wrapper around Mangum handler with custom logging
    """
    import logging
    import json

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Log incoming request
    logger.info(f"Incoming request: {json.dumps({
        'method': event.get('httpMethod'),
        'path': event.get('path'),
        'resource': event.get('resource'),
        'requestId': context.request_id if context else 'unknown'
    })}")

    try:
        # Call Mangum handler
        response = handler(event, context)

        # Log response
        logger.info(f"Response: {response.get('statusCode')}")

        return response

    except Exception as e:
        logger.error(f"Handler error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'internal_error',
                'message': str(e)
            })
        }


# Export both handlers
__all__ = ['handler', 'lambda_handler', 'handler_with_logging']
