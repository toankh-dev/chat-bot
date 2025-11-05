"""
Lambda Function: Vector Search Handler
Performs vector similarity search in OpenSearch Serverless

Updated to use environment-agnostic configuration (works with LocalStack and AWS)
"""

import json
import os
import sys
import logging
import time
from typing import Dict, List, Any, Optional

# Add common directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from config import get_settings
from llm import get_embedding_provider
from aws.opensearch_client import OpenSearchVectorClient
from utils.lambda_utils import (
    StructuredLogger,
    lambda_handler_decorator,
    measure_duration,
    cold_start_tracker
)

# Configure logging
settings = get_settings()
logger = logging.getLogger()
logger.setLevel(settings.log_level)
structured_logger = StructuredLogger("vector-search")

# Global clients (initialized once per Lambda container)
embedding_provider = None
opensearch_client = None

@measure_duration("client_initialization")
def initialize_clients():
    """Initialize clients with environment-aware configuration (reused across invocations)"""
    global embedding_provider, opensearch_client
    init_start = time.time()

    if embedding_provider is None:
        structured_logger.info(
            f"Initializing embedding provider",
            provider=settings.llm_provider
        )
        embedding_provider = get_embedding_provider()
        structured_logger.info(
            f"Embedding provider initialized",
            model_id=embedding_provider.model_id,
            dimension=embedding_provider.dimension
        )

    if opensearch_client is None:
        structured_logger.info("Initializing OpenSearch client")
        opensearch_client = OpenSearchVectorClient()
        structured_logger.info(
            "OpenSearch client initialized",
            endpoint=settings.opensearch_endpoint
        )

    # Track cold start
    init_duration = (time.time() - init_start) * 1000
    cold_start_tracker.record_cold_start(init_duration)

@lambda_handler_decorator(
    service_name="vector-search",
    log_event=False,
    log_response=False,
    capture_errors=False
)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for vector search

    Args:
        event: API Gateway proxy event or direct invocation event
        context: Lambda context

    Returns:
        API Gateway proxy response or search results
    """
    try:
        cold_start_tracker.increment_warm_invocation()
        # Initialize clients on cold start
        if embedding_provider is None or opensearch_client is None:
            initialize_clients()

        # Parse input
        if 'body' in event:
            # API Gateway proxy integration
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct invocation
            body = event

        # Handle health check
        if body.get('action') == 'health_check':
            return create_response(200, {'status': 'healthy'})

        # Extract search parameters
        query = body.get('query')
        if not query:
            return create_response(400, {'error': 'Missing required parameter: query'})

        k = body.get('k', 10)
        min_score = body.get('min_score', 0.0)
        filters = body.get('filters')
        search_type = body.get('search_type', 'vector')  # 'vector', 'keyword', or 'hybrid'

        logger.info(f"Search request: query='{query[:50]}...', k={k}, type={search_type}")

        # Generate query embedding using provider abstraction
        logger.info("Generating query embedding")
        try:
            embedding_response = embedding_provider.embed_text(query, task_type='retrieval_query')
            query_embedding = embedding_response.embedding
            logger.info(f"Generated embedding with dimension: {len(query_embedding)}")
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return create_response(500, {'error': 'Failed to generate query embedding'})

        # Perform search based on type
        if search_type == 'vector':
            # Pure vector search
            results = opensearch_client.search(
                query_vector=query_embedding,
                k=k,
                filter=filters,
                min_score=min_score
            )
        elif search_type == 'keyword':
            # Keyword search
            results = opensearch_client.keyword_search(
                query=query,
                k=k,
                filter=filters
            )
        elif search_type == 'hybrid':
            # Hybrid search (vector + keyword)
            results = opensearch_client.hybrid_search(
                query=query,
                query_vector=query_embedding,
                k=k,
                filter=filters,
                min_score=min_score
            )
        else:
            return create_response(400, {'error': f'Invalid search_type: {search_type}'})

        logger.info(f"Search completed: found {len(results)} results")

        # Format response
        response_data = {
            'query': query,
            'search_type': search_type,
            'results_count': len(results),
            'results': results
        }

        return create_response(200, response_data)

    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}", exc_info=True)
        return create_response(500, {'error': f'Internal server error: {str(e)}'})

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway proxy response

    Args:
        status_code: HTTP status code
        body: Response body

    Returns:
        API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }

# Example usage for testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'body': json.dumps({
            'query': 'What is the KASS system?',
            'k': 5,
            'search_type': 'hybrid'
        })
    }

    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = 'vector-search'
            self.memory_limit_in_mb = 1024
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:vector-search'
            self.aws_request_id = 'test-request-id'

    response = handler(test_event, MockContext())
    print(json.dumps(response, indent=2))
