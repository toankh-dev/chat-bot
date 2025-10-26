"""
Lambda function to fetch data from Discord
Alternative to GitLab/Slack/Backlog
"""

import json
import boto3
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import requests

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')


def get_secret(secret_name: str) -> Dict[str, Any]:
    """Retrieve secret from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise


def fetch_discord_messages(bot_token: str, channel_ids: List[str]) -> List[Dict]:
    """
    Fetch messages from Discord channels

    Args:
        bot_token: Discord bot token
        channel_ids: List of channel IDs to fetch from

    Returns:
        List of messages
    """
    messages = []
    headers = {
        'Authorization': f'Bot {bot_token}',
        'Content-Type': 'application/json'
    }

    for channel_id in channel_ids:
        try:
            logger.info(f"Fetching messages from channel: {channel_id}")

            # Get channel info first
            channel_url = f"https://discord.com/api/v10/channels/{channel_id}"
            channel_response = requests.get(channel_url, headers=headers, timeout=30)

            if channel_response.status_code != 200:
                logger.error(f"Failed to get channel {channel_id}: {channel_response.status_code}")
                continue

            channel_info = channel_response.json()
            channel_name = channel_info.get('name', 'unknown')

            # Get messages
            messages_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            params = {'limit': 100}  # Max 100 messages per request

            response = requests.get(messages_url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                channel_messages = response.json()

                # Add channel info to each message
                for msg in channel_messages:
                    msg['channel_name'] = channel_name
                    msg['channel_id'] = channel_id

                messages.extend(channel_messages)
                logger.info(f"Fetched {len(channel_messages)} messages from #{channel_name}")

            else:
                logger.error(f"Failed to fetch messages: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error fetching from channel {channel_id}: {str(e)}")
            continue

    logger.info(f"Total Discord messages fetched: {len(messages)}")
    return messages


def fetch_discord_threads(bot_token: str, guild_id: str) -> List[Dict]:
    """
    Fetch active threads from Discord server

    Args:
        bot_token: Discord bot token
        guild_id: Discord server (guild) ID

    Returns:
        List of threads
    """
    threads = []
    headers = {
        'Authorization': f'Bot {bot_token}',
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Fetching threads from guild: {guild_id}")

        url = f"https://discord.com/api/v10/guilds/{guild_id}/threads/active"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            threads = result.get('threads', [])
            logger.info(f"Fetched {len(threads)} active threads")

        else:
            logger.error(f"Failed to fetch threads: {response.status_code}")

    except Exception as e:
        logger.error(f"Error fetching threads: {str(e)}")

    return threads


def transform_to_documents(messages: List[Dict], threads: List[Dict]) -> List[Dict[str, Any]]:
    """
    Transform Discord data to document format for Knowledge Base

    Args:
        messages: List of Discord messages
        threads: List of Discord threads

    Returns:
        List of documents
    """
    documents = []

    # Transform messages
    for msg in messages:
        if not msg.get('content'):  # Skip empty messages
            continue

        doc = {
            'text': f"""# Discord Message in #{msg.get('channel_name', 'unknown')}

**Author**: {msg.get('author', {}).get('username', 'Unknown')}
**Timestamp**: {msg.get('timestamp', 'Unknown')}
**Channel**: #{msg.get('channel_name', 'unknown')}

## Message
{msg.get('content', '')}

**Message ID**: {msg.get('id', '')}
**Channel ID**: {msg.get('channel_id', '')}
""",
            'metadata': {
                'source': 'discord',
                'type': 'message',
                'channel': msg.get('channel_name', ''),
                'channel_id': msg.get('channel_id', ''),
                'author': msg.get('author', {}).get('username', ''),
                'message_id': msg.get('id', ''),
                'timestamp': msg.get('timestamp', '')
            }
        }
        documents.append(doc)

    # Transform threads
    for thread in threads:
        doc = {
            'text': f"""# Discord Thread: {thread.get('name', 'N/A')}

**Type**: Thread Discussion
**Created**: {thread.get('thread_metadata', {}).get('create_timestamp', 'N/A')}
**Message Count**: {thread.get('message_count', 0)}
**Member Count**: {thread.get('member_count', 0)}

## Thread Info
Thread ID: {thread.get('id', '')}
Parent Channel: {thread.get('parent_id', '')}
Archived: {thread.get('thread_metadata', {}).get('archived', False)}
""",
            'metadata': {
                'source': 'discord',
                'type': 'thread',
                'id': thread.get('id', ''),
                'name': thread.get('name', ''),
                'parent_id': thread.get('parent_id', ''),
                'created_at': thread.get('thread_metadata', {}).get('create_timestamp', '')
            }
        }
        documents.append(doc)

    logger.info(f"Transformed {len(documents)} documents from Discord")
    return documents


def upload_to_s3(bucket: str, prefix: str, documents: List[Dict[str, Any]]) -> int:
    """Upload documents to S3"""
    now = datetime.now(timezone.utc)
    date_path = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    timestamp = now.strftime('%Y%m%d_%H%M%S')

    uploaded_count = 0

    for idx, doc in enumerate(documents):
        key = f"{prefix}/{date_path}/discord_{timestamp}_doc_{idx}.json"

        try:
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(doc, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={k: str(v) for k, v in doc['metadata'].items()}
            )
            uploaded_count += 1
        except Exception as e:
            logger.error(f"Error uploading document {idx}: {str(e)}")
            continue

    logger.info(f"Uploaded {uploaded_count} documents to s3://{bucket}/{prefix}/{date_path}/")
    return uploaded_count


def lambda_handler(event, context):
    """Main Lambda handler for Discord data fetching"""
    logger.info("Starting Discord data fetch process...")

    try:
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable not set")

        # Check if Discord is enabled
        use_discord = os.environ.get('USE_DISCORD', 'true').lower() == 'true'

        if not use_discord:
            logger.info("Discord integration is disabled (USE_DISCORD=false)")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Discord integration disabled',
                    'total_documents': 0
                })
            }

        results = {
            'discord': {'docs': 0, 'status': 'not_attempted'}
        }

        # Fetch Discord data
        try:
            logger.info("Processing Discord data...")

            # Get credentials from environment (or Secrets Manager)
            discord_secret = get_secret('/chatbot/discord/bot-token')
            bot_token = discord_secret['bot_token']
            guild_id = discord_secret.get('guild_id', os.environ.get('DISCORD_GUILD_ID'))
            channel_ids_str = discord_secret.get('channel_ids', os.environ.get('DISCORD_CHANNEL_IDS', ''))

            # Parse channel IDs
            channel_ids = [cid.strip() for cid in channel_ids_str.split(',') if cid.strip()]

            if not channel_ids:
                logger.warning("No Discord channel IDs configured")
                results['discord'] = {'docs': 0, 'status': 'no_channels_configured'}
            else:
                # Fetch messages
                messages = fetch_discord_messages(bot_token, channel_ids)

                # Fetch threads (if guild_id provided)
                threads = []
                if guild_id:
                    threads = fetch_discord_threads(bot_token, guild_id)

                # Transform to documents
                discord_docs = transform_to_documents(messages, threads)

                # Upload to S3
                discord_count = upload_to_s3(bucket_name, 'discord', discord_docs)

                results['discord'] = {'docs': discord_count, 'status': 'success'}

        except Exception as e:
            logger.error(f"Discord processing failed: {str(e)}")
            results['discord'] = {'docs': 0, 'status': 'failed', 'error': str(e)}

        total_docs = sum(r['docs'] for r in results.values())
        success = any(r['status'] == 'success' for r in results.values())

        logger.info(f"Discord data fetch completed. Total documents: {total_docs}")

        return {
            'statusCode': 200 if success else 500,
            'body': json.dumps({
                'message': 'Discord data fetch completed',
                'total_documents': total_docs,
                'results': results,
                'bucket': bucket_name,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Discord data fetch failed', 'error': str(e)})
        }
