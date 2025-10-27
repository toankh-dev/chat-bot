"""
Lambda function to fetch data from GitLab, Slack, and Backlog APIs,
chunk the data, and save to S3.
S3 event will trigger embedder Lambda to process the chunked data.
"""

import json
import boto3
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any
import os
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Import chunking module
try:
    import sys
    sys.path.append('/opt/python')  # Lambda layer path
    from embeddings.chunk_router import chunk_data
    CHUNKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Chunking module not available: {e}")
    CHUNKING_AVAILABLE = False


def get_secret(secret_name: str) -> Dict[str, Any]:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise


def fetch_gitlab_data(token: str, base_url: str) -> Dict[str, List[Dict]]:
    """Fetch data from GitLab API."""
    headers = {'PRIVATE-TOKEN': token}
    data = {'issues': [], 'merge_requests': [], 'wikis': [], 'comments': []}

    try:
        # Fetch issues
        logger.info("Fetching GitLab issues...")
        page = 1
        while True:
            url = f"{base_url}/issues"
            params = {'page': page, 'per_page': 100, 'scope': 'all', 'state': 'all'}
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                break

            issues = response.json()
            if not issues:
                break

            data['issues'].extend(issues)
            page += 1
            if len(issues) < 100:
                break

        # Fetch merge requests
        logger.info("Fetching GitLab merge requests...")
        page = 1
        while True:
            url = f"{base_url}/merge_requests"
            params = {'page': page, 'per_page': 100, 'scope': 'all', 'state': 'all'}
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                break

            mrs = response.json()
            if not mrs:
                break

            data['merge_requests'].extend(mrs)
            page += 1
            if len(mrs) < 100:
                break

        logger.info(f"GitLab: {len(data['issues'])} issues, {len(data['merge_requests'])} MRs")

    except Exception as e:
        logger.error(f"Error fetching GitLab data: {str(e)}")
        raise

    return data


def fetch_slack_data(bot_token: str) -> Dict[str, List[Dict]]:
    """Fetch data from Slack API."""
    headers = {'Authorization': f'Bearer {bot_token}'}
    data = {'messages': [], 'channels': []}

    try:
        # Fetch channels
        logger.info("Fetching Slack channels...")
        url = "https://slack.com/api/conversations.list"
        params = {'exclude_archived': True, 'limit': 100}
        response = requests.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                data['channels'] = result.get('channels', [])

        # Fetch messages from channels
        logger.info("Fetching Slack messages...")
        for channel in data['channels'][:10]:  # Limit to 10 channels
            channel_id = channel['id']
            url = "https://slack.com/api/conversations.history"
            params = {'channel': channel_id, 'limit': 100}
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    messages = result.get('messages', [])
                    for msg in messages:
                        msg['channel_name'] = channel.get('name', '')
                        msg['channel_id'] = channel_id
                    data['messages'].extend(messages)

        logger.info(f"Slack: {len(data['channels'])} channels, {len(data['messages'])} messages")

    except Exception as e:
        logger.error(f"Error fetching Slack data: {str(e)}")
        raise

    return data


def fetch_backlog_data(api_key: str, space_url: str) -> Dict[str, List[Dict]]:
    """Fetch data from Backlog API."""
    params = {'apiKey': api_key}
    data = {'issues': [], 'wikis': [], 'comments': []}

    try:
        # Fetch issues
        logger.info("Fetching Backlog issues...")
        offset = 0
        while True:
            url = f"{space_url}/api/v2/issues"
            params_with_offset = {**params, 'count': 100, 'offset': offset}
            response = requests.get(url, params=params_with_offset, timeout=30)

            if response.status_code != 200:
                break

            issues = response.json()
            if not issues:
                break

            data['issues'].extend(issues)
            offset += 100
            if len(issues) < 100:
                break

        # Fetch wikis
        logger.info("Fetching Backlog wikis...")
        url = f"{space_url}/api/v2/wikis"
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data['wikis'] = response.json()

        logger.info(f"Backlog: {len(data['issues'])} issues, {len(data['wikis'])} wikis")

    except Exception as e:
        logger.error(f"Error fetching Backlog data: {str(e)}")
        raise

    return data


def transform_to_documents(source: str, data: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
    """Transform API data to document format for Knowledge Base."""
    documents = []

    if source == 'gitlab':
        # Transform issues
        for issue in data.get('issues', []):
            doc = {
                'text': f"""# GitLab Issue: {issue.get('title', 'N/A')}

**Project**: {issue.get('project_id', 'N/A')}
**Status**: {issue.get('state', 'N/A')}
**Author**: {issue.get('author', {}).get('username', 'N/A')}
**Created**: {issue.get('created_at', 'N/A')}
**Labels**: {', '.join(issue.get('labels', []))}

## Description
{issue.get('description', 'No description')}

**URL**: {issue.get('web_url', '')}
""",
                'metadata': {
                    'source': 'gitlab',
                    'type': 'issue',
                    'id': str(issue.get('id', '')),
                    'url': issue.get('web_url', ''),
                    'created_at': issue.get('created_at', ''),
                    'author': issue.get('author', {}).get('username', ''),
                    'project_id': str(issue.get('project_id', ''))
                }
            }
            documents.append(doc)

        # Transform merge requests
        for mr in data.get('merge_requests', []):
            doc = {
                'text': f"""# GitLab Merge Request: {mr.get('title', 'N/A')}

**Project**: {mr.get('project_id', 'N/A')}
**Status**: {mr.get('state', 'N/A')}
**Author**: {mr.get('author', {}).get('username', 'N/A')}
**Source**: {mr.get('source_branch', 'N/A')} → **Target**: {mr.get('target_branch', 'N/A')}
**Created**: {mr.get('created_at', 'N/A')}

## Description
{mr.get('description', 'No description')}

**URL**: {mr.get('web_url', '')}
""",
                'metadata': {
                    'source': 'gitlab',
                    'type': 'merge_request',
                    'id': str(mr.get('id', '')),
                    'url': mr.get('web_url', ''),
                    'created_at': mr.get('created_at', ''),
                    'author': mr.get('author', {}).get('username', ''),
                    'project_id': str(mr.get('project_id', ''))
                }
            }
            documents.append(doc)

    elif source == 'slack':
        # Transform messages
        for msg in data.get('messages', []):
            if msg.get('text'):  # Skip empty messages
                doc = {
                    'text': f"""# Slack Message in #{msg.get('channel_name', 'unknown')}

**User**: {msg.get('user', 'Unknown')}
**Timestamp**: {datetime.fromtimestamp(float(msg.get('ts', 0))).isoformat()}

## Message
{msg.get('text', '')}

**Channel**: #{msg.get('channel_name', 'unknown')}
**Channel ID**: {msg.get('channel_id', '')}
""",
                    'metadata': {
                        'source': 'slack',
                        'type': 'message',
                        'channel': msg.get('channel_name', ''),
                        'channel_id': msg.get('channel_id', ''),
                        'user': msg.get('user', ''),
                        'timestamp': msg.get('ts', '')
                    }
                }
                documents.append(doc)

    elif source == 'backlog':
        # Transform issues
        for issue in data.get('issues', []):
            doc = {
                'text': f"""# Backlog Issue: {issue.get('summary', 'N/A')}

**Key**: {issue.get('issueKey', 'N/A')}
**Project**: {issue.get('projectId', 'N/A')}
**Status**: {issue.get('status', {}).get('name', 'N/A')}
**Priority**: {issue.get('priority', {}).get('name', 'N/A')}
**Assignee**: {issue.get('assignee', {}).get('name', 'Unassigned') if issue.get('assignee') else 'Unassigned'}
**Created**: {issue.get('created', 'N/A')}

## Description
{issue.get('description', 'No description')}

**URL**: {issue.get('url', '')}
""",
                'metadata': {
                    'source': 'backlog',
                    'type': 'issue',
                    'id': str(issue.get('id', '')),
                    'key': issue.get('issueKey', ''),
                    'url': issue.get('url', ''),
                    'created_at': issue.get('created', ''),
                    'author': issue.get('createdUser', {}).get('name', ''),
                    'project_id': str(issue.get('projectId', ''))
                }
            }
            documents.append(doc)

        # Transform wikis
        for wiki in data.get('wikis', []):
            doc = {
                'text': f"""# Backlog Wiki: {wiki.get('name', 'N/A')}

**Project**: {wiki.get('projectId', 'N/A')}
**Created**: {wiki.get('created', 'N/A')}

## Content
{wiki.get('content', 'No content')}

**URL**: {wiki.get('url', '')}
""",
                'metadata': {
                    'source': 'backlog',
                    'type': 'wiki',
                    'id': str(wiki.get('id', '')),
                    'url': wiki.get('url', ''),
                    'created_at': wiki.get('created', ''),
                    'author': wiki.get('createdUser', {}).get('name', ''),
                    'project_id': str(wiki.get('projectId', ''))
                }
            }
            documents.append(doc)

    logger.info(f"Transformed {len(documents)} documents from {source}")
    return documents


def chunk_and_upload_to_s3(bucket: str, prefix: str, documents: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Chunk documents and upload to S3.
    Returns stats about chunking and upload.
    """
    now = datetime.now(timezone.utc)
    date_path = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    batch_id = f"{timestamp}_{os.urandom(4).hex()}"

    stats = {
        'original_docs': len(documents),
        'total_chunks': 0,
        'uploaded': 0,
        'errors': 0
    }

    all_chunks = []

    # Chunk all documents
    if CHUNKING_AVAILABLE:
        logger.info(f"Chunking {len(documents)} documents...")
        for doc in documents:
            try:
                source_type = doc.get('metadata', {}).get('source', 'text')
                text = doc.get('text', '')

                if not text:
                    logger.warning(f"Empty text in document, skipping")
                    continue

                # Chunk based on source type
                chunks = chunk_data(source_type, text)

                for chunk in chunks:
                    # Merge original metadata with chunk metadata
                    merged_metadata = {**doc.get('metadata', {}), **chunk.get('metadata', {})}
                    all_chunks.append({
                        'text': chunk['text'],
                        'metadata': merged_metadata
                    })

            except Exception as e:
                logger.error(f"Error chunking document: {e}")
                stats['errors'] += 1
                continue

        stats['total_chunks'] = len(all_chunks)
        logger.info(f"Chunked into {len(all_chunks)} pieces")
    else:
        # If chunking not available, treat each document as a chunk
        all_chunks = documents
        stats['total_chunks'] = len(documents)
        logger.warning("Chunking not available, uploading documents as-is")

    # Upload chunks to S3
    # Group all chunks into a single batch file for efficient processing
    batch_key = f"{prefix}/chunked/{date_path}/batch_{batch_id}.json"

    try:
        batch_data = {
            'batch_id': batch_id,
            'timestamp': now.isoformat(),
            'source': prefix,
            'chunk_count': len(all_chunks),
            'chunks': all_chunks
        }

        s3_client.put_object(
            Bucket=bucket,
            Key=batch_key,
            Body=json.dumps(batch_data, ensure_ascii=False, indent=2),
            ContentType='application/json',
            Metadata={
                'batch_id': batch_id,
                'source': prefix,
                'chunk_count': str(len(all_chunks)),
                'timestamp': timestamp
            }
        )
        stats['uploaded'] = len(all_chunks)
        logger.info(f"Uploaded batch with {len(all_chunks)} chunks to s3://{bucket}/{batch_key}")

    except Exception as e:
        logger.error(f"Error uploading batch: {str(e)}")
        stats['errors'] += 1

    return stats




def lambda_handler(event, context):
    """
    Main Lambda handler - fetches, chunks, and saves data to S3.
    S3 event will trigger embedder Lambda.
    """
    logger.info("Starting data fetch and chunk process...")

    try:
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable not set")

        results = {
            'gitlab': {'docs': 0, 'chunks': 0, 'status': 'not_attempted'},
            'slack': {'docs': 0, 'chunks': 0, 'status': 'not_attempted'},
            'backlog': {'docs': 0, 'chunks': 0, 'status': 'not_attempted'}
        }

        # Fetch GitLab data
        try:
            logger.info("Processing GitLab data...")
            gitlab_secret = get_secret('/chatbot/gitlab/api-token')
            gitlab_data = fetch_gitlab_data(gitlab_secret['token'], gitlab_secret['base_url'])
            gitlab_docs = transform_to_documents('gitlab', gitlab_data)

            # Chunk and upload
            gitlab_stats = chunk_and_upload_to_s3(bucket_name, 'gitlab', gitlab_docs)
            results['gitlab'] = {
                'docs': gitlab_stats['original_docs'],
                'chunks': gitlab_stats['total_chunks'],
                'uploaded': gitlab_stats['uploaded'],
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"GitLab processing failed: {str(e)}")
            results['gitlab'] = {'docs': 0, 'chunks': 0, 'status': 'failed', 'error': str(e)}

        # Fetch Slack data
        try:
            logger.info("Processing Slack data...")
            slack_secret = get_secret('/chatbot/slack/bot-token')
            slack_data = fetch_slack_data(slack_secret['bot_token'])
            slack_docs = transform_to_documents('slack', slack_data)

            # Chunk and upload
            slack_stats = chunk_and_upload_to_s3(bucket_name, 'slack', slack_docs)
            results['slack'] = {
                'docs': slack_stats['original_docs'],
                'chunks': slack_stats['total_chunks'],
                'uploaded': slack_stats['uploaded'],
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Slack processing failed: {str(e)}")
            results['slack'] = {'docs': 0, 'chunks': 0, 'status': 'failed', 'error': str(e)}

        # Fetch Backlog data
        try:
            logger.info("Processing Backlog data...")
            backlog_secret = get_secret('/chatbot/backlog/api-key')
            backlog_data = fetch_backlog_data(backlog_secret['api_key'], backlog_secret['space_url'])
            backlog_docs = transform_to_documents('backlog', backlog_data)

            # Chunk and upload
            backlog_stats = chunk_and_upload_to_s3(bucket_name, 'backlog', backlog_docs)
            results['backlog'] = {
                'docs': backlog_stats['original_docs'],
                'chunks': backlog_stats['total_chunks'],
                'uploaded': backlog_stats['uploaded'],
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Backlog processing failed: {str(e)}")
            results['backlog'] = {'docs': 0, 'chunks': 0, 'status': 'failed', 'error': str(e)}

        total_docs = sum(r['docs'] for r in results.values() if r['docs'] > 0)
        total_chunks = sum(r['chunks'] for r in results.values() if r['chunks'] > 0)
        success = any(r['status'] == 'success' for r in results.values())

        logger.info(f"Data fetch completed. Total: {total_docs} docs → {total_chunks} chunks")

        return {
            'statusCode': 200 if success else 500,
            'body': json.dumps({
                'message': 'Data fetch and chunk completed',
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'results': results,
                'bucket': bucket_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'note': 'Chunked data uploaded to S3. Embedder Lambda will be triggered automatically.'
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Data fetch failed', 'error': str(e)})
        }
