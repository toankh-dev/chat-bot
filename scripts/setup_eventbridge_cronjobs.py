"""
Setup EventBridge rules for scheduled Lambda execution
Creates cronjobs for:
1. Data fetching (Slack, GitLab, Backlog, Discord)
2. Data embedding (process fetched data)
"""

import boto3
import json
import sys
import os
from datetime import datetime

# Initialize AWS clients
events_client = boto3.client('events', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))
lambda_client = boto3.client('lambda', endpoint_url=os.environ.get('AWS_ENDPOINT_URL'))


def create_eventbridge_rule(rule_name: str, schedule_expression: str, description: str) -> str:
    """
    Create or update EventBridge rule

    Args:
        rule_name: Name of the rule
        schedule_expression: Cron or rate expression
        description: Rule description

    Returns:
        Rule ARN
    """
    try:
        response = events_client.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule_expression,
            State='ENABLED',
            Description=description
        )
        print(f"✓ Created/updated rule: {rule_name}")
        print(f"  Schedule: {schedule_expression}")
        print(f"  ARN: {response['RuleArn']}")
        return response['RuleArn']

    except Exception as e:
        print(f"✗ Error creating rule {rule_name}: {e}")
        raise


def add_lambda_permission(function_name: str, rule_arn: str, statement_id: str):
    """
    Add permission for EventBridge to invoke Lambda

    Args:
        function_name: Lambda function name
        rule_arn: EventBridge rule ARN
        statement_id: Unique statement ID
    """
    try:
        # Remove existing permission if exists
        try:
            lambda_client.remove_permission(
                FunctionName=function_name,
                StatementId=statement_id
            )
        except:
            pass

        # Add new permission
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn
        )
        print(f"✓ Added permission for {function_name}")

    except Exception as e:
        print(f"✗ Error adding permission: {e}")
        raise


def add_target_to_rule(rule_name: str, target_id: str, lambda_arn: str, input_data: dict = None):
    """
    Add Lambda target to EventBridge rule

    Args:
        rule_name: Name of the rule
        target_id: Unique target ID
        lambda_arn: Lambda function ARN
        input_data: Optional input JSON for Lambda
    """
    try:
        target = {
            'Id': target_id,
            'Arn': lambda_arn
        }

        if input_data:
            target['Input'] = json.dumps(input_data)

        events_client.put_targets(
            Rule=rule_name,
            Targets=[target]
        )
        print(f"✓ Added target to rule: {rule_name}")

    except Exception as e:
        print(f"✗ Error adding target: {e}")
        raise


def get_lambda_arn(function_name: str) -> str:
    """
    Get Lambda function ARN

    Args:
        function_name: Lambda function name

    Returns:
        Function ARN
    """
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"✗ Error getting Lambda ARN for {function_name}: {e}")
        raise


def setup_data_fetcher_cronjob():
    """
    Setup cronjob for data_fetcher Lambda
    Runs every 6 hours to fetch fresh data from APIs
    """
    print("\n" + "="*60)
    print("Setting up Data Fetcher Cronjob")
    print("="*60)

    rule_name = "chatbot-data-fetcher-schedule"
    function_name = "chatbot-data-fetcher"

    # Create rule - runs every 6 hours
    schedule = "rate(6 hours)"
    description = "Fetch data from Slack, GitLab, and Backlog every 6 hours"

    rule_arn = create_eventbridge_rule(rule_name, schedule, description)

    # Get Lambda ARN
    lambda_arn = get_lambda_arn(function_name)

    # Add permission
    add_lambda_permission(function_name, rule_arn, f"{rule_name}-permission")

    # Add target
    add_target_to_rule(rule_name, "1", lambda_arn)

    print(f"✓ Data fetcher cronjob setup complete")


def setup_discord_fetcher_cronjob():
    """
    Setup cronjob for discord_fetcher Lambda
    Runs every 6 hours to fetch Discord messages
    """
    print("\n" + "="*60)
    print("Setting up Discord Fetcher Cronjob")
    print("="*60)

    rule_name = "chatbot-discord-fetcher-schedule"
    function_name = "chatbot-discord-fetcher"

    # Create rule - runs every 6 hours
    schedule = "rate(6 hours)"
    description = "Fetch Discord messages every 6 hours"

    rule_arn = create_eventbridge_rule(rule_name, schedule, description)

    # Get Lambda ARN
    lambda_arn = get_lambda_arn(function_name)

    # Add permission
    add_lambda_permission(function_name, rule_arn, f"{rule_name}-permission")

    # Add target
    add_target_to_rule(rule_name, "1", lambda_arn)

    print(f"✓ Discord fetcher cronjob setup complete")


def setup_embedder_cronjob():
    """
    NOTE: This function is deprecated as embedding is now integrated into data_fetcher.
    Keeping for backward compatibility but does nothing.
    """
    print("\n" + "="*60)
    print("Embedder Cronjob (DEPRECATED)")
    print("="*60)
    print("ℹ️  Embedding is now integrated into data_fetcher Lambda")
    print("ℹ️  No separate embedder cronjob needed")
    print("✓ Skipped embedder setup (deprecated)")


def setup_manual_trigger_rule():
    """
    Setup rule for manual triggering via EventBridge console
    """
    print("\n" + "="*60)
    print("Setting up Manual Trigger Rules")
    print("="*60)

    # Manual data fetcher trigger (with embedding)
    rule_name = "chatbot-data-fetcher-manual"
    function_name = "chatbot-data-fetcher"
    description = "Manual trigger for data fetcher with embedding (disabled by default)"

    # Create disabled rule
    try:
        response = events_client.put_rule(
            Name=rule_name,
            State='DISABLED',
            Description=description,
            EventPattern=json.dumps({
                "source": ["chatbot.manual"],
                "detail-type": ["Manual Trigger"]
            })
        )
        rule_arn = response['RuleArn']
        print(f"✓ Created manual trigger rule: {rule_name}")

        # Get Lambda ARN and add target with embedding enabled
        lambda_arn = get_lambda_arn(function_name)
        add_lambda_permission(function_name, rule_arn, f"{rule_name}-permission")

        # Add target with input to enable embedding
        input_data = {
            "embed_immediately": True,
            "skip_s3": False
        }
        add_target_to_rule(rule_name, "1", lambda_arn, input_data)

    except Exception as e:
        print(f"✗ Error creating manual rule: {e}")


def list_all_rules():
    """
    List all EventBridge rules for chatbot
    """
    print("\n" + "="*60)
    print("Current EventBridge Rules")
    print("="*60)

    try:
        response = events_client.list_rules(NamePrefix="chatbot-")

        if not response.get('Rules'):
            print("No rules found")
            return

        for rule in response['Rules']:
            print(f"\nRule: {rule['Name']}")
            print(f"  State: {rule['State']}")
            print(f"  Schedule: {rule.get('ScheduleExpression', 'N/A')}")
            print(f"  Description: {rule.get('Description', 'N/A')}")

            # Get targets
            targets_response = events_client.list_targets_by_rule(Rule=rule['Name'])
            for target in targets_response.get('Targets', []):
                print(f"  Target: {target['Arn']}")

    except Exception as e:
        print(f"✗ Error listing rules: {e}")


def main():
    """
    Main function to setup all cronjobs
    """
    print("\n" + "="*60)
    print("EventBridge Cronjob Setup")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)

    try:
        # Setup all cronjobs
        setup_data_fetcher_cronjob()
        setup_discord_fetcher_cronjob()
        setup_embedder_cronjob()
        setup_manual_trigger_rule()

        # List all rules
        list_all_rules()

        print("\n" + "="*60)
        print("✅ All cronjobs setup successfully!")
        print("="*60)
        print("\nSchedule Summary:")
        print("  - Data Fetcher: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)")
        print("    • Fetches data from Slack, GitLab, Backlog")
        print("    • Chunks and embeds data immediately")
        print("    • Stores in ChromaDB")
        print("  - Discord Fetcher: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)")
        print("\nManual Execution:")
        print("  # Trigger with embedding")
        print("  aws --endpoint-url=http://localhost:4566 lambda invoke \\")
        print("    --function-name chatbot-data-fetcher \\")
        print("    --payload '{\"embed_immediately\": true}' \\")
        print("    response.json")
        print("\n  # Trigger without embedding (S3 only)")
        print("  aws --endpoint-url=http://localhost:4566 lambda invoke \\")
        print("    --function-name chatbot-data-fetcher \\")
        print("    --payload '{\"embed_immediately\": false}' \\")
        print("    response.json")
        print("\nDisable a rule:")
        print("  aws events disable-rule --name chatbot-data-fetcher-schedule")

        return 0

    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
