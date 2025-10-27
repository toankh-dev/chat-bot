#!/usr/bin/env python3
"""
Unified deployment script for the embedding system
Handles: Lambda deployment, EventBridge setup, S3 triggers, and secrets
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import zipfile
import boto3
from pathlib import Path
from datetime import datetime


# ============================================================================
# Configuration
# ============================================================================

LOCALSTACK_ENDPOINT = os.environ.get('AWS_ENDPOINT_URL', 'http://localhost:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-1')

LAMBDA_FUNCTIONS = [
    {
        "name": "data_fetcher",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Fetch and chunk data from GitLab, Slack, and Backlog",
        "timeout": 300,
        "memory_size": 512,
        "env": {"S3_BUCKET_NAME": "chatbot-knowledge-base"}
    },
    {
        "name": "discord_fetcher",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Fetch data from Discord channels",
        "timeout": 300,
        "memory_size": 512,
        "env": {"S3_BUCKET_NAME": "chatbot-knowledge-base"}
    },
    {
        "name": "embedder",
        "handler": "lambda_function.lambda_handler",
        "runtime": "python3.11",
        "description": "Embed chunked data into ChromaDB (S3 triggered)",
        "timeout": 900,
        "memory_size": 1024,
        "env": {
            "CHROMADB_HOST": "chromadb",
            "CHROMADB_PORT": "8000"
        }
    }
]

SECRETS = [
    {
        "name": "/chatbot/slack/bot-token",
        "value": {"bot_token": "xoxb-your-slack-bot-token"}
    },
    {
        "name": "/chatbot/gitlab/api-token",
        "value": {
            "token": "your-gitlab-token",
            "base_url": "https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID"
        }
    },
    {
        "name": "/chatbot/backlog/api-key",
        "value": {
            "api_key": "your-backlog-api-key",
            "space_url": "https://your-space.backlog.com"
        }
    },
    {
        "name": "/chatbot/discord/bot-token",
        "value": {
            "bot_token": "your-discord-bot-token",
            "guild_id": "your-guild-id",
            "channel_ids": "channel-id-1,channel-id-2"
        }
    },
    {
        "name": "/chatbot/voyage/api-key",
        "value": {"api_key": "your-voyage-api-key"}
    }
]

S3_BUCKET = "chatbot-knowledge-base"


# ============================================================================
# AWS Clients
# ============================================================================

lambda_client = boto3.client('lambda', endpoint_url=LOCALSTACK_ENDPOINT, region_name=AWS_REGION)
events_client = boto3.client('events', endpoint_url=LOCALSTACK_ENDPOINT, region_name=AWS_REGION)
s3_client = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT, region_name=AWS_REGION)
secrets_client = boto3.client('secretsmanager', endpoint_url=LOCALSTACK_ENDPOINT, region_name=AWS_REGION)


# ============================================================================
# Helper Functions
# ============================================================================

def print_section(title):
    """Print formatted section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def run_command(cmd, description=""):
    """Run shell command"""
    if description:
        print(f"  {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


# ============================================================================
# 1. Lambda Deployment
# ============================================================================

def create_lambda_zip(function_name: str) -> Path:
    """Create Lambda deployment package"""
    lambda_dir = Path("lambda") / function_name
    temp_dir = Path(tempfile.mkdtemp())

    print(f"  📦 Packaging {function_name}...")

    # Copy Lambda code
    shutil.copytree(lambda_dir, temp_dir, dirs_exist_ok=True)

    # Install dependencies
    requirements = temp_dir / "requirements.txt"
    if requirements.exists():
        print(f"     Installing dependencies...")
        subprocess.run(
            ["pip", "install", "-r", str(requirements), "-t", str(temp_dir), "--quiet"],
            check=True
        )

    # Create zip
    zip_path = Path(tempfile.gettempdir()) / f"{function_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)

    # Cleanup
    shutil.rmtree(temp_dir)

    print(f"     ✓ Created {zip_path.name}")
    return zip_path


def deploy_lambda(config: dict):
    """Deploy Lambda function"""
    function_name = f"chatbot-{config['name']}"

    print(f"\n  🚀 Deploying {function_name}...")

    # Create zip
    zip_path = create_lambda_zip(config['name'])

    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"     ✓ Updated function code")

        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=config['handler'],
            Runtime=config['runtime'],
            Timeout=config.get('timeout', 60),
            MemorySize=config.get('memory_size', 128),
            Environment={'Variables': config.get('env', {})}
        )
        print(f"     ✓ Updated configuration")

    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime=config['runtime'],
            Role='arn:aws:iam::000000000000:role/lambda-role',
            Handler=config['handler'],
            Code={'ZipFile': zip_content},
            Description=config['description'],
            Timeout=config.get('timeout', 60),
            MemorySize=config.get('memory_size', 128),
            Environment={'Variables': config.get('env', {})}
        )
        print(f"     ✓ Created new function")

    # Cleanup
    zip_path.unlink()


def deploy_all_lambdas():
    """Deploy all Lambda functions"""
    print_section("1. DEPLOYING LAMBDA FUNCTIONS")

    for config in LAMBDA_FUNCTIONS:
        deploy_lambda(config)

    print(f"\n  ✅ Deployed {len(LAMBDA_FUNCTIONS)} Lambda functions")


# ============================================================================
# 2. EventBridge Setup
# ============================================================================

def setup_eventbridge():
    """Setup EventBridge scheduled rules"""
    print_section("2. SETTING UP EVENTBRIDGE RULES")

    rules = [
        {
            "name": "chatbot-data-fetcher-schedule",
            "schedule": "rate(6 hours)",
            "description": "Fetch, chunk data from Slack, GitLab, Backlog",
            "target": "chatbot-data-fetcher"
        },
        {
            "name": "chatbot-discord-fetcher-schedule",
            "schedule": "rate(6 hours)",
            "description": "Fetch Discord messages",
            "target": "chatbot-discord-fetcher"
        }
    ]

    for rule in rules:
        print(f"\n  ⏰ Creating rule: {rule['name']}")

        # Create rule
        response = events_client.put_rule(
            Name=rule['name'],
            ScheduleExpression=rule['schedule'],
            State='ENABLED',
            Description=rule['description']
        )
        print(f"     ✓ Rule created: {rule['schedule']}")

        # Get Lambda ARN
        lambda_response = lambda_client.get_function(FunctionName=rule['target'])
        lambda_arn = lambda_response['Configuration']['FunctionArn']

        # Add Lambda permission
        try:
            lambda_client.remove_permission(
                FunctionName=rule['target'],
                StatementId=f"{rule['name']}-permission"
            )
        except:
            pass

        lambda_client.add_permission(
            FunctionName=rule['target'],
            StatementId=f"{rule['name']}-permission",
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=response['RuleArn']
        )
        print(f"     ✓ Added Lambda permission")

        # Add target
        events_client.put_targets(
            Rule=rule['name'],
            Targets=[{'Id': '1', 'Arn': lambda_arn}]
        )
        print(f"     ✓ Added target: {rule['target']}")

    print(f"\n  ✅ EventBridge rules configured")


# ============================================================================
# 3. S3 Setup
# ============================================================================

def setup_s3():
    """Setup S3 bucket and event notifications"""
    print_section("3. SETTING UP S3 BUCKET & TRIGGERS")

    # Create bucket
    print(f"  📦 Creating S3 bucket: {S3_BUCKET}")
    try:
        s3_client.create_bucket(Bucket=S3_BUCKET)
        print(f"     ✓ Bucket created")
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"     ✓ Bucket already exists")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"     ✓ Bucket already exists")

    # Get embedder Lambda ARN
    lambda_response = lambda_client.get_function(FunctionName='chatbot-embedder')
    lambda_arn = lambda_response['Configuration']['FunctionArn']

    # Add Lambda permission for S3
    print(f"\n  🔐 Adding S3 invoke permission...")
    try:
        lambda_client.remove_permission(
            FunctionName='chatbot-embedder',
            StatementId=f's3-invoke-{S3_BUCKET}'
        )
    except:
        pass

    lambda_client.add_permission(
        FunctionName='chatbot-embedder',
        StatementId=f's3-invoke-{S3_BUCKET}',
        Action='lambda:InvokeFunction',
        Principal='s3.amazonaws.com',
        SourceArn=f'arn:aws:s3:::{S3_BUCKET}'
    )
    print(f"     ✓ Permission added")

    # Configure S3 notification
    print(f"\n  📬 Configuring S3 event notifications...")
    notification_config = {
        'LambdaFunctionConfigurations': [
            {
                'Id': 'embedder-trigger',
                'LambdaFunctionArn': lambda_arn,
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'prefix', 'Value': 'chunked/'},
                            {'Name': 'suffix', 'Value': '.json'}
                        ]
                    }
                }
            }
        ]
    }

    s3_client.put_bucket_notification_configuration(
        Bucket=S3_BUCKET,
        NotificationConfiguration=notification_config
    )
    print(f"     ✓ S3 → Lambda trigger configured")
    print(f"     • Trigger: s3:ObjectCreated:* on */chunked/*.json")

    print(f"\n  ✅ S3 setup complete")


# ============================================================================
# 4. Secrets Manager
# ============================================================================

def setup_secrets():
    """Create secrets in Secrets Manager"""
    print_section("4. SETTING UP SECRETS MANAGER")

    for secret in SECRETS:
        print(f"\n  🔑 Creating secret: {secret['name']}")
        secret_value = json.dumps(secret['value'])

        try:
            secrets_client.create_secret(
                Name=secret['name'],
                SecretString=secret_value
            )
            print(f"     ✓ Secret created")
        except secrets_client.exceptions.ResourceExistsException:
            print(f"     ✓ Secret already exists")

    print(f"\n  ✅ {len(SECRETS)} secrets configured")


# ============================================================================
# 5. Verification
# ============================================================================

def verify_deployment():
    """Verify deployment"""
    print_section("5. VERIFYING DEPLOYMENT")

    # Check Lambdas
    print("  📋 Lambda Functions:")
    response = lambda_client.list_functions()
    for func in response['Functions']:
        if func['FunctionName'].startswith('chatbot-'):
            print(f"     ✓ {func['FunctionName']}")

    # Check EventBridge
    print("\n  📋 EventBridge Rules:")
    response = events_client.list_rules(NamePrefix='chatbot-')
    for rule in response['Rules']:
        print(f"     ✓ {rule['Name']} ({rule.get('ScheduleExpression', 'N/A')})")

    # Check S3
    print("\n  📋 S3 Buckets:")
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"     ✓ {S3_BUCKET}")
    except:
        print(f"     ✗ {S3_BUCKET} not found")

    print("\n  ✅ Verification complete")


# ============================================================================
# Main
# ============================================================================

def main():
    """Main deployment function"""
    print_section("EMBEDDING SYSTEM DEPLOYMENT")
    print(f"  Endpoint: {LOCALSTACK_ENDPOINT}")
    print(f"  Region: {AWS_REGION}")
    print(f"  Time: {datetime.now().isoformat()}")

    try:
        # Deploy all components
        deploy_all_lambdas()
        setup_eventbridge()
        setup_s3()
        setup_secrets()
        verify_deployment()

        # Summary
        print_section("✅ DEPLOYMENT COMPLETE")
        print("""
  System Architecture:
    EventBridge (every 6h) → data_fetcher Lambda
                         → Fetch & Chunk → S3
                         → S3 Event → embedder Lambda
                         → Embed → ChromaDB

  Next Steps:
    1. Update secrets with real API tokens:
       aws --endpoint-url={0} secretsmanager update-secret \\
         --secret-id /chatbot/slack/bot-token \\
         --secret-string '{{"bot_token": "xoxb-real-token"}}'

    2. Manually trigger data fetch:
       aws --endpoint-url={0} lambda invoke \\
         --function-name chatbot-data-fetcher response.json

    3. Monitor logs:
       aws --endpoint-url={0} logs tail \\
         /aws/lambda/chatbot-data-fetcher --follow

    4. Check ChromaDB:
       docker exec chatbot-app python -c "
       import chromadb
       client = chromadb.HttpClient(host='chromadb', port=8000)
       collection = client.get_collection('chatbot_knowledge')
       print(f'Total: {{collection.count()}} embeddings')
       "
        """.format(LOCALSTACK_ENDPOINT))

        return 0

    except Exception as e:
        print(f"\n  ✗ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
