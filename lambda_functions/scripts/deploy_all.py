#!/usr/bin/env python3
"""
Deployment Script: Deploy Lambda Functions and Layers to AWS
Automates the deployment of Lambda layers and functions
"""

import boto3
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
NAME_PREFIX = os.getenv('NAME_PREFIX', 'kass-chatbot-dev')
PYTHON_RUNTIME = 'python3.11'

# Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
DIST_DIR = ROOT_DIR / 'dist'

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)

def print_header(message: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)

def print_step(message: str):
    """Print a step message"""
    print(f"\n→ {message}")

def print_success(message: str):
    """Print a success message"""
    print(f"✓ {message}")

def print_error(message: str):
    """Print an error message"""
    print(f"✗ ERROR: {message}", file=sys.stderr)

def deploy_layer(layer_name: str, zip_path: Path, description: str) -> Optional[str]:
    """
    Deploy a Lambda layer

    Args:
        layer_name: Name of the layer
        zip_path: Path to the layer zip file
        description: Layer description

    Returns:
        Layer version ARN if successful, None otherwise
    """
    print_step(f"Deploying layer: {layer_name}")

    if not zip_path.exists():
        print_error(f"Layer zip file not found: {zip_path}")
        return None

    try:
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

        # Publish layer version
        response = lambda_client.publish_layer_version(
            LayerName=f"{NAME_PREFIX}-{layer_name}",
            Description=description,
            Content={'ZipFile': zip_content},
            CompatibleRuntimes=[PYTHON_RUNTIME]
        )

        layer_arn = response['LayerVersionArn']
        print_success(f"Layer deployed: {layer_arn}")
        return layer_arn

    except Exception as e:
        print_error(f"Failed to deploy layer {layer_name}: {str(e)}")
        return None

def deploy_function(function_name: str, zip_path: Path, handler: str,
                     description: str, layer_arns: List[str],
                     environment_vars: Dict[str, str], timeout: int = 300,
                     memory_size: int = 1024) -> bool:
    """
    Deploy a Lambda function

    Args:
        function_name: Name of the function
        zip_path: Path to the function zip file
        handler: Function handler
        description: Function description
        layer_arns: List of layer ARNs
        environment_vars: Environment variables
        timeout: Function timeout in seconds
        memory_size: Memory size in MB

    Returns:
        True if successful, False otherwise
    """
    print_step(f"Deploying function: {function_name}")

    if not zip_path.exists():
        print_error(f"Function zip file not found: {zip_path}")
        return False

    full_function_name = f"{NAME_PREFIX}-{function_name}"

    try:
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

        # Check if function exists
        function_exists = False
        try:
            lambda_client.get_function(FunctionName=full_function_name)
            function_exists = True
        except lambda_client.exceptions.ResourceNotFoundException:
            pass

        if function_exists:
            # Update existing function
            print(f"  Updating existing function...")

            # Update function code
            lambda_client.update_function_code(
                FunctionName=full_function_name,
                ZipFile=zip_content
            )

            # Wait for update to complete
            waiter = lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName=full_function_name)

            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=full_function_name,
                Runtime=PYTHON_RUNTIME,
                Handler=handler,
                Timeout=timeout,
                MemorySize=memory_size,
                Environment={'Variables': environment_vars},
                Layers=layer_arns
            )

            print_success(f"Function updated: {full_function_name}")

        else:
            # Create new function
            print(f"  Creating new function...")

            # Note: This requires an IAM role ARN
            # In production, this should be passed as a parameter
            print_error("Function creation not implemented - use Terraform for initial deployment")
            return False

        return True

    except Exception as e:
        print_error(f"Failed to deploy function {function_name}: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print_header("KASS Chatbot Lambda Deployment")

    # Check if dist directory exists
    if not DIST_DIR.exists():
        print_error(f"Distribution directory not found: {DIST_DIR}")
        print("Run build_layers.ps1 and package_lambdas.ps1 first")
        sys.exit(1)

    # ========================================================================
    # Deploy Lambda Layers
    # ========================================================================

    print_header("Deploying Lambda Layers")

    layers_dir = DIST_DIR / 'layers'
    layer_arns = {}

    # Common utilities layer
    common_layer_path = layers_dir / 'common-utilities.zip'
    if common_layer_path.exists():
        arn = deploy_layer(
            'common-utilities',
            common_layer_path,
            'Common utilities for KASS Chatbot (boto3, opensearch-py, etc.)'
        )
        if arn:
            layer_arns['common'] = arn
    else:
        print_error(f"Common utilities layer not found: {common_layer_path}")

    # LangChain layer
    langchain_layer_path = layers_dir / 'langchain.zip'
    if langchain_layer_path.exists():
        arn = deploy_layer(
            'langchain',
            langchain_layer_path,
            'LangChain framework and dependencies'
        )
        if arn:
            layer_arns['langchain'] = arn
    else:
        print_error(f"LangChain layer not found: {langchain_layer_path}")

    # Document processing layer
    doc_layer_path = layers_dir / 'document-processing.zip'
    if doc_layer_path.exists():
        arn = deploy_layer(
            'document-processing',
            doc_layer_path,
            'Document processing libraries (pypdf, python-docx, openpyxl)'
        )
        if arn:
            layer_arns['document'] = arn
    else:
        print_error(f"Document processing layer not found: {doc_layer_path}")

    # ========================================================================
    # Deploy Lambda Functions
    # ========================================================================

    print_header("Deploying Lambda Functions")

    functions_dir = DIST_DIR / 'functions'

    # Common environment variables (from environment or defaults)
    common_env_vars = {
        'AWS_REGION': REGION,
        'BEDROCK_MODEL_ID': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
        'BEDROCK_EMBED_MODEL_ID': os.getenv('BEDROCK_EMBED_MODEL_ID', 'amazon.titan-embed-text-v2:0'),
        'OPENSEARCH_ENDPOINT': os.getenv('OPENSEARCH_ENDPOINT', ''),
        'OPENSEARCH_COLLECTION_ID': os.getenv('OPENSEARCH_COLLECTION_ID', ''),
        'OPENSEARCH_INDEX_NAME': os.getenv('OPENSEARCH_INDEX_NAME', 'knowledge_base'),
        'CONVERSATIONS_TABLE': os.getenv('CONVERSATIONS_TABLE', f'{NAME_PREFIX}-conversations'),
        'CACHE_TABLE': os.getenv('CACHE_TABLE', f'{NAME_PREFIX}-cache'),
        'DOCUMENTS_BUCKET': os.getenv('DOCUMENTS_BUCKET', f'{NAME_PREFIX}-documents'),
    }

    # Check required environment variables
    if not common_env_vars['OPENSEARCH_ENDPOINT']:
        print_error("OPENSEARCH_ENDPOINT environment variable not set")
        print("Deploy OpenSearch collection first using Terraform")

    # Orchestrator function
    orchestrator_path = functions_dir / 'orchestrator.zip'
    if orchestrator_path.exists() and 'common' in layer_arns and 'langchain' in layer_arns:
        deploy_function(
            'orchestrator',
            orchestrator_path,
            'handler.handler',
            'KASS Chatbot orchestrator with LangChain agent',
            [layer_arns['common'], layer_arns['langchain']],
            common_env_vars,
            timeout=300,
            memory_size=1024
        )

    # Vector search function
    vector_search_path = functions_dir / 'vector_search.zip'
    if vector_search_path.exists() and 'common' in layer_arns:
        deploy_function(
            'vector-search',
            vector_search_path,
            'handler.handler',
            'Vector similarity search in OpenSearch',
            [layer_arns['common']],
            common_env_vars,
            timeout=60,
            memory_size=512
        )

    # Document processor function
    doc_processor_path = functions_dir / 'document_processor.zip'
    if doc_processor_path.exists() and 'common' in layer_arns and 'document' in layer_arns:
        deploy_function(
            'document-processor',
            doc_processor_path,
            'handler.handler',
            'Process and index documents from S3',
            [layer_arns['common'], layer_arns['document']],
            {**common_env_vars, 'CHUNK_SIZE': '1000', 'CHUNK_OVERLAP': '200'},
            timeout=300,
            memory_size=2048
        )

    # ========================================================================
    # Summary
    # ========================================================================

    print_header("Deployment Summary")

    print(f"\nLayers deployed: {len(layer_arns)}")
    for name, arn in layer_arns.items():
        print(f"  - {name}: {arn}")

    print("\n✓ Deployment complete!")
    print("\nNext steps:")
    print("1. Update API Gateway integration with Lambda function ARNs")
    print("2. Configure EventBridge rules for document processing")
    print("3. Test endpoints:")
    print(f"   POST /chat - Orchestrator")
    print(f"   POST /search - Vector search")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Deployment failed: {str(e)}")
        sys.exit(1)
