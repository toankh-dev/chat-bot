"""
Conversation Management Lambda Handler
"""

from mangum import Mangum
from app import app

# Mangum adapter for AWS Lambda
handler = Mangum(app, lifespan="off")
lambda_handler = handler
