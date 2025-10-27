"""
Setup S3 event notifications to trigger embedder Lambda
when chunked data is uploaded
"""

import boto3
import json
import sys
import os

# Initialize AWS clients
s3_client = boto3.client('s3', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))
lambda_client = boto3.client('lambda', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))


def get_lambda_arn(function_name: str) -> str:
    """Get Lambda function ARN"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"✗ Error getting Lambda ARN: {e}")
        raise


def add_lambda_permission(function_name: str, bucket_name: str):
    """Add permission for S3 to invoke Lambda"""
    try:
        # Remove existing permission if exists
        try:
            lambda_client.remove_permission(
                FunctionName=function_name,
                StatementId=f's3-invoke-{bucket_name}'
            )
        except:
            pass

        # Add new permission
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f's3-invoke-{bucket_name}',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{bucket_name}'
        )
        print(f"✓ Added S3 invoke permission for {function_name}")

    except Exception as e:
        print(f"✗ Error adding permission: {e}")
        raise


def setup_s3_notification(bucket_name: str, lambda_arn: str):
    """
    Setup S3 bucket notification to trigger Lambda
    when new chunked files are uploaded
    """
    try:
        # Notification configuration
        # Trigger when files are created in */chunked/* prefix
        notification_config = {
            'LambdaFunctionConfigurations': [
                {
                    'Id': 'embedder-trigger',
                    'LambdaFunctionArn': lambda_arn,
                    'Events': ['s3:ObjectCreated:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': 'chunked/'  # Only trigger for chunked files
                                },
                                {
                                    'Name': 'suffix',
                                    'Value': '.json'
                                }
                            ]
                        }
                    }
                }
            ]
        }

        # Apply notification configuration
        s3_client.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_config
        )

        print(f"✓ S3 notification configured for bucket: {bucket_name}")
        print(f"  Trigger: s3:ObjectCreated:* on */chunked/*.json")
        print(f"  Lambda: {lambda_arn}")

    except Exception as e:
        print(f"✗ Error setting up S3 notification: {e}")
        raise


def verify_setup(bucket_name: str):
    """Verify S3 notification configuration"""
    try:
        response = s3_client.get_bucket_notification_configuration(
            Bucket=bucket_name
        )

        print("\n" + "="*60)
        print("Current S3 Notification Configuration")
        print("="*60)
        print(json.dumps(response, indent=2, default=str))

    except Exception as e:
        print(f"✗ Error verifying setup: {e}")


def main():
    """Main function"""
    print("\n" + "="*60)
    print("S3 Event Trigger Setup for Embedder Lambda")
    print("="*60)

    bucket_name = "chatbot-knowledge-base"
    function_name = "chatbot-embedder"

    try:
        # Get Lambda ARN
        print(f"\n1. Getting Lambda ARN for {function_name}...")
        lambda_arn = get_lambda_arn(function_name)
        print(f"   ARN: {lambda_arn}")

        # Add Lambda permission
        print(f"\n2. Adding S3 invoke permission...")
        add_lambda_permission(function_name, bucket_name)

        # Setup S3 notification
        print(f"\n3. Configuring S3 bucket notification...")
        setup_s3_notification(bucket_name, lambda_arn)

        # Verify
        print(f"\n4. Verifying configuration...")
        verify_setup(bucket_name)

        print("\n" + "="*60)
        print("✅ S3 Trigger Setup Complete!")
        print("="*60)
        print("\nHow it works:")
        print("  1. data_fetcher Lambda fetches and chunks data")
        print("  2. Chunked data saved to s3://bucket/*/chunked/batch_*.json")
        print("  3. S3 automatically triggers embedder Lambda")
        print("  4. embedder Lambda embeds chunks and stores in ChromaDB")
        print("\nTest manually:")
        print(f"  aws --endpoint-url=http://localhost:4566 lambda invoke \\")
        print(f"    --function-name {function_name} \\")
        print(f"    --payload file://test_s3_event.json \\")
        print(f"    response.json")

        return 0

    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
