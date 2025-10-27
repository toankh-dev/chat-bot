#!/usr/bin/env python3
"""
Deploy Lambda functions to LocalStack
"""

import os
import subprocess
import tempfile
import shutil
import zipfile
from pathlib import Path

LOCALSTACK_ENDPOINT = "http://localhost:4566"
AWS_REGION = "ap-southeast-1"

LAMBDA_FUNCTIONS = [
    {
        "name": "data_fetcher",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Fetch and chunk data from GitLab, Slack, and Backlog",
        "timeout": 300,  # 5 minutes for fetching + chunking
        "memory_size": 512  # 512MB memory
    },
    {
        "name": "discord_fetcher",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Fetch data from Discord channels",
        "timeout": 300,
        "memory_size": 512
    },
    {
        "name": "embedder",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Embed chunked data into ChromaDB (S3 triggered)",
        "timeout": 900,  # 15 minutes for embedding
        "memory_size": 1024  # 1GB memory for embedding
    }
]


def create_lambda_zip(function_name: str, temp_dir: Path) -> Path:
    """Create a zip file for Lambda deployment"""
    lambda_dir = Path("lambda") / function_name

    print(f"   Copying Lambda code from {lambda_dir}...")

    # Copy all files from lambda directory
    shutil.copytree(lambda_dir, temp_dir, dirs_exist_ok=True)

    # Install dependencies if requirements.txt exists
    requirements_file = temp_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"   Installing dependencies...")
        subprocess.run(
            ["pip", "install", "-r", str(requirements_file), "-t", str(temp_dir), "--quiet"],
            check=True
        )

    # Create zip file
    zip_path = Path(tempfile.gettempdir()) / f"{function_name}.zip"
    print(f"   Creating zip file: {zip_path}...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)

    return zip_path


def deploy_lambda(function_config: dict):
    """Deploy a Lambda function to LocalStack"""
    function_name = function_config["name"]

    print(f"\n[PACKAGE] {function_name}...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create Lambda zip
        zip_path = create_lambda_zip(function_name, temp_path)

        # Delete function if exists
        print(f"   Deleting old function if exists...")
        subprocess.run(
            [
                "aws", "--endpoint-url", LOCALSTACK_ENDPOINT,
                "--region", AWS_REGION,
                "lambda", "delete-function",
                "--function-name", function_name
            ],
            stderr=subprocess.DEVNULL
        )

        # Create Lambda function
        print(f"   Deploying to LocalStack...")
        result = subprocess.run(
            [
                "aws", "--endpoint-url", LOCALSTACK_ENDPOINT,
                "--region", AWS_REGION,
                "lambda", "create-function",
                "--function-name", function_name,
                "--runtime", function_config["runtime"],
                "--handler", function_config["handler"],
                "--role", "arn:aws:iam::000000000000:role/lambda-role",
                "--zip-file", f"fileb://{zip_path}",
                "--description", function_config["description"],
                "--timeout", "300",
                "--memory-size", "512",
                "--environment", f"Variables={{LOCALSTACK_ENDPOINT={LOCALSTACK_ENDPOINT}}}"
            ],
            capture_output=True,
            text=True
        )

        # Cleanup
        if zip_path.exists():
            zip_path.unlink()

        if result.returncode == 0:
            print(f"   [OK] {function_name} deployed successfully")
        else:
            print(f"   [FAIL] Failed to deploy {function_name}")
            print(f"   Error: {result.stderr}")


def main():
    print("Deploying Lambda functions to LocalStack...")

    # Deploy all functions
    for func_config in LAMBDA_FUNCTIONS:
        try:
            deploy_lambda(func_config)
        except Exception as e:
            print(f"   [ERROR] Error deploying {func_config['name']}: {e}")

    # List deployed functions
    print("\nDeployment complete!")
    print("\nList of deployed functions:")
    subprocess.run(
        [
            "aws", "--endpoint-url", LOCALSTACK_ENDPOINT,
            "--region", AWS_REGION,
            "lambda", "list-functions",
            "--query", "Functions[].FunctionName",
            "--output", "table"
        ]
    )


if __name__ == "__main__":
    main()
