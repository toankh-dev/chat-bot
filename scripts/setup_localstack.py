"""
Setup LocalStack AWS services for local development
"""

import boto3
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LocalStack configuration
LOCALSTACK_ENDPOINT = "http://localhost:4566"
REGION = "ap-southeast-1"

# Initialize clients
s3 = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT, region_name=REGION)
dynamodb = boto3.client('dynamodb', endpoint_url=LOCALSTACK_ENDPOINT, region_name=REGION)
secrets = boto3.client('secretsmanager', endpoint_url=LOCALSTACK_ENDPOINT, region_name=REGION)
events = boto3.client('events', endpoint_url=LOCALSTACK_ENDPOINT, region_name=REGION)
lambda_client = boto3.client('lambda', endpoint_url=LOCALSTACK_ENDPOINT, region_name=REGION)


def create_s3_buckets():
    """Create S3 buckets for data storage"""
    buckets = [
        'chatbot-raw-data',
        'chatbot-processed-data',
        'chatbot-backups'
    ]

    for bucket in buckets:
        try:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
            logger.info(f"✅ Created S3 bucket: {bucket}")
        except s3.exceptions.BucketAlreadyOwnedByYou:
            logger.info(f"⏭️  S3 bucket already exists: {bucket}")
        except Exception as e:
            logger.error(f"❌ Failed to create bucket {bucket}: {e}")


def create_dynamodb_tables():
    """Create DynamoDB tables"""
    tables = [
        {
            'TableName': 'chatbot-conversations',
            'KeySchema': [
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'user-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            'BillingMode': 'PROVISIONED',
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ]

    for table_config in tables:
        table_name = table_config['TableName']
        try:
            dynamodb.create_table(**table_config)
            logger.info(f"✅ Created DynamoDB table: {table_name}")

            # Wait for table to be active
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            logger.info(f"✅ Table {table_name} is active")

        except dynamodb.exceptions.ResourceInUseException:
            logger.info(f"⏭️  DynamoDB table already exists: {table_name}")
        except Exception as e:
            logger.error(f"❌ Failed to create table {table_name}: {e}")


def create_secrets():
    """Create secrets in Secrets Manager"""
    secrets_list = [
        {
            'Name': '/chatbot/gitlab/api-token',
            'SecretString': json.dumps({
                'token': 'your_gitlab_token_here',
                'base_url': 'https://gitlab.com/api/v4'
            })
        },
        {
            'Name': '/chatbot/slack/bot-token',
            'SecretString': json.dumps({
                'bot_token': 'xoxb-your-slack-token-here',
                'signing_secret': 'your_signing_secret_here'
            })
        },
        {
            'Name': '/chatbot/backlog/api-key',
            'SecretString': json.dumps({
                'api_key': 'your_backlog_api_key_here',
                'space_url': 'https://your_space.backlog.com'
            })
        }
    ]

    for secret in secrets_list:
        try:
            secrets.create_secret(**secret)
            logger.info(f"✅ Created secret: {secret['Name']}")
        except secrets.exceptions.ResourceExistsException:
            logger.info(f"⏭️  Secret already exists: {secret['Name']}")
            # Update existing secret
            try:
                secrets.put_secret_value(
                    SecretId=secret['Name'],
                    SecretString=secret['SecretString']
                )
                logger.info(f"✅ Updated secret: {secret['Name']}")
            except Exception as e:
                logger.error(f"❌ Failed to update secret {secret['Name']}: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to create secret {secret['Name']}: {e}")


def verify_setup():
    """Verify all services are set up correctly"""
    logger.info("\n" + "="*60)
    logger.info("Verifying setup...")
    logger.info("="*60)

    # Check S3 buckets
    try:
        buckets = s3.list_buckets()
        logger.info(f"\n📦 S3 Buckets: {len(buckets['Buckets'])}")
        for bucket in buckets['Buckets']:
            logger.info(f"  - {bucket['Name']}")
    except Exception as e:
        logger.error(f"❌ Failed to list S3 buckets: {e}")

    # Check DynamoDB tables
    try:
        tables = dynamodb.list_tables()
        logger.info(f"\n🗄️  DynamoDB Tables: {len(tables['TableNames'])}")
        for table in tables['TableNames']:
            logger.info(f"  - {table}")
    except Exception as e:
        logger.error(f"❌ Failed to list DynamoDB tables: {e}")

    # Check Secrets
    try:
        secret_list = secrets.list_secrets()
        logger.info(f"\n🔐 Secrets: {len(secret_list['SecretList'])}")
        for secret in secret_list['SecretList']:
            logger.info(f"  - {secret['Name']}")
    except Exception as e:
        logger.error(f"❌ Failed to list secrets: {e}")

    logger.info("\n" + "="*60)
    logger.info("✅ Setup verification complete!")
    logger.info("="*60)


def main():
    """Main setup function"""
    logger.info("🚀 Starting LocalStack setup...")
    logger.info(f"Endpoint: {LOCALSTACK_ENDPOINT}")
    logger.info(f"Region: {REGION}")

    # Wait for LocalStack to be ready
    logger.info("\n⏳ Waiting for LocalStack to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            s3.list_buckets()
            logger.info("✅ LocalStack is ready!")
            break
        except Exception as e:
            if i == max_retries - 1:
                logger.error("❌ LocalStack is not responding. Please check docker-compose logs.")
                return
            logger.info(f"Waiting... ({i+1}/{max_retries})")
            time.sleep(2)

    # Create resources
    logger.info("\n📦 Creating S3 buckets...")
    create_s3_buckets()

    logger.info("\n🗄️  Creating DynamoDB tables...")
    create_dynamodb_tables()

    logger.info("\n🔐 Creating secrets...")
    create_secrets()

    # Verify setup
    verify_setup()

    logger.info("\n🎉 LocalStack setup complete!")
    logger.info("\n📝 Next steps:")
    logger.info("  1. Update secrets with real API keys:")
    logger.info("     python scripts/update_secrets.py")
    logger.info("  2. Run data fetcher:")
    logger.info("     python scripts/run_data_fetcher.py")
    logger.info("  3. Build vector index:")
    logger.info("     python scripts/build_vector_index.py")


if __name__ == "__main__":
    main()
