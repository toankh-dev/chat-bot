"""
AWS Lambda handler for REST API using Mangum.

This handler wraps the FastAPI application for deployment on AWS Lambda with API Gateway.
"""

from mangum import Mangum
from main import app
from core.logger import logger

# Create Lambda handler with API Gateway event format
handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path="/prod"  # Adjust based on your API Gateway stage
)

logger.info("Lambda API handler initialized with routes:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        logger.info(f"  {', '.join(route.methods)} {route.path}")
