"""
DynamoDB client for managing NoSQL operations.
"""

import boto3
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from src.core.config import settings
from src.core.logger import logger
from src.core.errors import DatabaseError, ResourceNotFoundError


class DynamoDBClient:
    """
    DynamoDB client wrapper providing high-level operations.

    Handles connection management, error handling, and common query patterns.
    """

    def __init__(self):
        """Initialize DynamoDB client."""
        self._client = None
        self._resource = None

    @property
    def client(self):
        """Get or create DynamoDB client."""
        if self._client is None:
            config = {}
            if settings.DYNAMODB_ENDPOINT:
                config['endpoint_url'] = settings.DYNAMODB_ENDPOINT

            self._client = boto3.client(
                'dynamodb',
                region_name=settings.AWS_REGION,
                **config
            )
        return self._client

    @property
    def resource(self):
        """Get or create DynamoDB resource."""
        if self._resource is None:
            config = {}
            if settings.DYNAMODB_ENDPOINT:
                config['endpoint_url'] = settings.DYNAMODB_ENDPOINT

            self._resource = boto3.resource(
                'dynamodb',
                region_name=settings.AWS_REGION,
                **config
            )
        return self._resource

    def get_table(self, table_name: str):
        """Get DynamoDB table resource."""
        return self.resource.Table(table_name)

    async def put_item(
        self,
        table_name: str,
        item: Dict[str, Any],
        condition_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Put an item into DynamoDB table.

        Args:
            table_name: Name of the table
            item: Item to insert
            condition_expression: Optional condition for the put operation

        Returns:
            The response from DynamoDB

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)
            kwargs = {'Item': item}

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = table.put_item(**kwargs)
            logger.info(f"Item inserted into {table_name}")
            return response

        except ClientError as e:
            logger.error(f"Error putting item to {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to insert item into {table_name}",
                details={"error": str(e)}
            )

    async def get_item(
        self,
        table_name: str,
        key: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB table.

        Args:
            table_name: Name of the table
            key: Primary key of the item

        Returns:
            The item if found, None otherwise

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')

        except ClientError as e:
            logger.error(f"Error getting item from {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get item from {table_name}",
                details={"error": str(e), "key": key}
            )

    async def query(
        self,
        table_name: str,
        key_condition_expression,
        filter_expression=None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_index_forward: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query items from DynamoDB table.

        Args:
            table_name: Name of the table
            key_condition_expression: Key condition for query
            filter_expression: Optional filter expression
            index_name: Optional GSI name
            limit: Maximum number of items to return
            scan_index_forward: Sort order (True=ascending, False=descending)

        Returns:
            List of items matching the query

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)
            kwargs = {
                'KeyConditionExpression': key_condition_expression,
                'ScanIndexForward': scan_index_forward
            }

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression
            if index_name:
                kwargs['IndexName'] = index_name
            if limit:
                kwargs['Limit'] = limit

            response = table.query(**kwargs)
            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response and (limit is None or len(items) < limit):
                kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.query(**kwargs)
                items.extend(response.get('Items', []))

            return items

        except ClientError as e:
            logger.error(f"Error querying {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to query {table_name}",
                details={"error": str(e)}
            )

    async def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        condition_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an item in DynamoDB table.

        Args:
            table_name: Name of the table
            key: Primary key of the item
            update_expression: Update expression
            expression_attribute_values: Values for the update expression
            expression_attribute_names: Optional attribute name mappings
            condition_expression: Optional condition for the update

        Returns:
            The updated item

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)
            kwargs = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'ALL_NEW'
            }

            if expression_attribute_names:
                kwargs['ExpressionAttributeNames'] = expression_attribute_names
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = table.update_item(**kwargs)
            return response.get('Attributes', {})

        except ClientError as e:
            logger.error(f"Error updating item in {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to update item in {table_name}",
                details={"error": str(e), "key": key}
            )

    async def delete_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        condition_expression: Optional[str] = None
    ) -> None:
        """
        Delete an item from DynamoDB table.

        Args:
            table_name: Name of the table
            key: Primary key of the item
            condition_expression: Optional condition for the delete

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)
            kwargs = {'Key': key}

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            table.delete_item(**kwargs)
            logger.info(f"Item deleted from {table_name}")

        except ClientError as e:
            logger.error(f"Error deleting item from {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete item from {table_name}",
                details={"error": str(e), "key": key}
            )

    async def batch_write(
        self,
        table_name: str,
        items: List[Dict[str, Any]]
    ) -> None:
        """
        Batch write items to DynamoDB table.

        Args:
            table_name: Name of the table
            items: List of items to write (max 25)

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            table = self.get_table(table_name)

            with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)

            logger.info(f"Batch write completed for {len(items)} items to {table_name}")

        except ClientError as e:
            logger.error(f"Error in batch write to {table_name}: {str(e)}")
            raise DatabaseError(
                message=f"Failed to batch write to {table_name}",
                details={"error": str(e), "item_count": len(items)}
            )


# Singleton instance
_dynamo_client = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get singleton DynamoDB client instance."""
    global _dynamo_client
    if _dynamo_client is None:
        _dynamo_client = DynamoDBClient()
    return _dynamo_client
