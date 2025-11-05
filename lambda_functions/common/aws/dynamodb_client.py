"""
Amazon DynamoDB Client
Conversation and state management
"""

import logging
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.config import Config

from .config import get_settings, create_client, AWSClientFactory

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for Amazon DynamoDB operations"""

    def __init__(self, region: str = None, factory: AWSClientFactory = None):
        """
        Initialize DynamoDB client with environment-aware configuration.

        Args:
            region: AWS region (optional, uses settings default)
            factory: AWS client factory (optional, uses global factory)
        """
        self.settings = get_settings()
        self.region = region or self.settings.aws_region
        self.factory = factory or AWSClientFactory()

        # Initialize DynamoDB resource and client using factory
        self.dynamodb = self.factory.create_resource('dynamodb', self.region)
        self.client = self.factory.create_client('dynamodb', self.region)

        logger.info(f"Initialized DynamoDB client in {self.region} (environment: {self.settings.environment.value})")

    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        return self.dynamodb.Table(table_name)


class ConversationStore:
    """Store and retrieve conversation history"""

    def __init__(self, table_name: str, dynamodb_client: DynamoDBClient = None):
        """
        Initialize conversation store

        Args:
            table_name: DynamoDB table name for conversations
            dynamodb_client: DynamoDB client instance
        """
        self.client = dynamodb_client or DynamoDBClient()
        self.table = self.client.get_table(table_name)
        logger.info(f"Initialized ConversationStore with table: {table_name}")

    def save_message(
        self,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_days: int = 30
    ) -> Dict[str, Any]:
        """
        Save a message to conversation history

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            role: Message role (user or assistant)
            content: Message content
            metadata: Optional metadata
            ttl_days: TTL in days (default 30)

        Returns:
            Saved item
        """
        try:
            timestamp = int(time.time() * 1000)  # Milliseconds
            ttl = int(time.time()) + (ttl_days * 24 * 60 * 60)

            item = {
                'conversation_id': conversation_id,
                'timestamp': timestamp,
                'user_id': user_id,
                'role': role,
                'content': content,
                'metadata': metadata or {},
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'ttl': ttl
            }

            self.table.put_item(Item=item)
            logger.info(f"Saved message to conversation {conversation_id}")

            return item

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    def get_conversation(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return

        Returns:
            List of messages sorted by timestamp
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('conversation_id').eq(conversation_id),
                Limit=limit,
                ScanIndexForward=True  # Oldest first
            )

            messages = response.get('Items', [])
            logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")

            return messages

        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return []

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user

        Args:
            user_id: User ID
            limit: Maximum number of conversations

        Returns:
            List of conversation summaries
        """
        try:
            response = self.table.query(
                IndexName='user_id-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                Limit=limit,
                ScanIndexForward=False  # Newest first
            )

            conversations = response.get('Items', [])
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")

            # Group by conversation_id and get the latest message
            conv_dict = {}
            for item in conversations:
                conv_id = item['conversation_id']
                if conv_id not in conv_dict:
                    conv_dict[conv_id] = item

            return list(conv_dict.values())

        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation (all messages)

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful
        """
        try:
            # Query all items
            response = self.table.query(
                KeyConditionExpression=Key('conversation_id').eq(conversation_id)
            )

            items = response.get('Items', [])

            # Batch delete
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={
                            'conversation_id': item['conversation_id'],
                            'timestamp': item['timestamp']
                        }
                    )

            logger.info(f"Deleted {len(items)} messages from conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False


class AgentStateStore:
    """Store and retrieve agent execution state"""

    def __init__(self, table_name: str, dynamodb_client: DynamoDBClient = None):
        """
        Initialize agent state store

        Args:
            table_name: DynamoDB table name for agent state
            dynamodb_client: DynamoDB client instance
        """
        self.client = dynamodb_client or DynamoDBClient()
        self.table = self.client.get_table(table_name)
        logger.info(f"Initialized AgentStateStore with table: {table_name}")

    def save_state(
        self,
        agent_id: str,
        execution_id: str,
        state: Dict[str, Any],
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        intermediate_steps: Optional[List[Dict[str, Any]]] = None,
        ttl_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Save agent execution state

        Args:
            agent_id: Agent ID
            execution_id: Execution ID
            state: Agent state dictionary
            tool_calls: List of tool calls
            intermediate_steps: List of intermediate steps
            ttl_hours: TTL in hours

        Returns:
            Saved item
        """
        try:
            timestamp = int(time.time())
            ttl = timestamp + (ttl_hours * 60 * 60)

            item = {
                'agent_id': agent_id,
                'execution_id': execution_id,
                'state': state,
                'tool_calls': tool_calls or [],
                'intermediate_steps': intermediate_steps or [],
                'created_at': timestamp,
                'ttl': ttl
            }

            self.table.put_item(Item=item)
            logger.info(f"Saved state for agent {agent_id}, execution {execution_id}")

            return item

        except Exception as e:
            logger.error(f"Error saving agent state: {e}")
            raise

    def get_state(
        self,
        agent_id: str,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent execution state

        Args:
            agent_id: Agent ID
            execution_id: Execution ID

        Returns:
            Agent state or None
        """
        try:
            response = self.table.get_item(
                Key={
                    'agent_id': agent_id,
                    'execution_id': execution_id
                }
            )

            item = response.get('Item')
            if item:
                logger.info(f"Retrieved state for agent {agent_id}, execution {execution_id}")
            else:
                logger.info(f"No state found for agent {agent_id}, execution {execution_id}")

            return item

        except Exception as e:
            logger.error(f"Error getting agent state: {e}")
            return None


class CacheStore:
    """Cache store for response caching"""

    def __init__(self, table_name: str, dynamodb_client: DynamoDBClient = None):
        """
        Initialize cache store

        Args:
            table_name: DynamoDB table name for cache
            dynamodb_client: DynamoDB client instance
        """
        self.client = dynamodb_client or DynamoDBClient()
        self.table = self.client.get_table(table_name)
        logger.info(f"Initialized CacheStore with table: {table_name}")

    def get_cached_response(
        self,
        query_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response

        Args:
            query_hash: Hash of query

        Returns:
            Cached response or None
        """
        try:
            response = self.table.get_item(
                Key={'query_hash': query_hash}
            )

            item = response.get('Item')

            if item:
                # Check if expired
                if int(time.time()) > item.get('ttl', 0):
                    logger.info(f"Cache expired for query {query_hash}")
                    return None

                logger.info(f"Cache hit for query {query_hash}")
                return item.get('response')

            logger.info(f"Cache miss for query {query_hash}")
            return None

        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    def cache_response(
        self,
        query_hash: str,
        query: str,
        response: Any,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Cache a response

        Args:
            query_hash: Hash of query
            query: Original query
            response: Response to cache
            ttl_seconds: TTL in seconds

        Returns:
            True if successful
        """
        try:
            timestamp = int(time.time())
            ttl = timestamp + ttl_seconds

            item = {
                'query_hash': query_hash,
                'query': query,
                'response': response,
                'cached_at': timestamp,
                'ttl': ttl
            }

            self.table.put_item(Item=item)
            logger.info(f"Cached response for query {query_hash}")

            return True

        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False


def python_obj_to_dynamodb(obj: Any) -> Any:
    """
    Convert Python objects to DynamoDB-compatible types

    Args:
        obj: Python object

    Returns:
        DynamoDB-compatible object
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: python_obj_to_dynamodb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [python_obj_to_dynamodb(item) for item in obj]
    else:
        return obj


def dynamodb_to_python_obj(obj: Any) -> Any:
    """
    Convert DynamoDB types to Python objects

    Args:
        obj: DynamoDB object

    Returns:
        Python object
    """
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    elif isinstance(obj, dict):
        return {k: dynamodb_to_python_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [dynamodb_to_python_obj(item) for item in obj]
    else:
        return obj
