#!/usr/bin/env python3
"""
Deploy Lambda Functions and Layers to AWS
Deploys Lambda layers and updates function code
Note: Use Terraform for initial infrastructure setup
"""

import boto3
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
NAME_PREFIX = os.getenv('NAME_PREFIX', 'kass-chatbot-dev')
PYTHON_RUNTIME = 'python3.11'

# Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent
DIST_DIR = ROOT_DIR / 'terraform' / 'dist'

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
    """Deploy a Lambda layer"""
    print_step(f"Deploying layer: {layer_name}")

    if not zip_path.exists():
        print_error(f"Layer zip file not found: {zip_path}")
        return None

    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

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

def update_function_code(function_name: str, zip_path: Path) -> bool:
    """Update Lambda function code"""
    print_step(f"Updating function: {function_name}")

    if not zip_path.exists():
        print_error(f"Function zip file not found: {zip_path}")
        return False

    full_function_name = f"{NAME_PREFIX}-{function_name}"

    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=full_function_name)
        except lambda_client.exceptions.ResourceNotFoundException:
            print_error(f"Function not found: {full_function_name}")
            print("  Deploy infrastructure with Terraform first")
            return False

        # Update function code
        lambda_client.update_function_code(
            FunctionName=full_function_name,
            ZipFile=zip_content
        )

        # Wait for update to complete
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=full_function_name)

        print_success(f"Function updated: {full_function_name}")
        return True

    except Exception as e:
        print_error(f"Failed to update function {function_name}: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print_header("KASS Lambda Deployment")

    # Check if dist directory exists
    if not DIST_DIR.exists():
        print_error(f"Distribution directory not found: {DIST_DIR}")
        print("Run: powershell scripts/lambda/build-all.ps1")
        sys.exit(1)

    # Deploy Lambda Layers
    print_header("Deploying Lambda Layers")

    layers_dir = DIST_DIR / 'layers'
    layer_arns = {}

    layers_to_deploy = [
        ('common-utilities', 'Common utilities (boto3, opensearch-py, etc.)'),
        ('langchain', 'LangChain framework and dependencies'),
        ('document-processing', 'Document processing libraries (pypdf, python-docx, openpyxl)')
    ]

    for layer_name, description in layers_to_deploy:
        layer_path = layers_dir / f'{layer_name}.zip'
        if layer_path.exists():
            arn = deploy_layer(layer_name, layer_path, description)
            if arn:
                layer_arns[layer_name] = arn

    # Update Lambda Functions
    print_header("Updating Lambda Functions")

    functions_dir = DIST_DIR / 'functions'

    functions_to_update = [
        'orchestrator',
        'vector_search',
        'document_processor',
        'report_tool',
        'summarize_tool',
        'code_review_tool',
        'discord_handler'
    ]

    updated_count = 0
    for function_name in functions_to_update:
        function_path = functions_dir / f'{function_name}.zip'
        if function_path.exists():
            if update_function_code(function_name, function_path):
                updated_count += 1

    # Summary
    print_header("Deployment Summary")
    print(f"\nLayers deployed: {len(layer_arns)}")
    for name, arn in layer_arns.items():
        print(f"  - {name}")

    print(f"\nFunctions updated: {updated_count}/{len(functions_to_update)}")
    print("\n✓ Deployment complete!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Deployment failed: {str(e)}")
        sys.exit(1)
