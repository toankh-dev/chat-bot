"""
DynamoDB implementation of ConversationRepository.
"""
from typing import Optional, List
from src.shared.repositories.conversation_repository import ConversationRepository
from src.domain.entities.conversation import Conversation

from src.infrastructure.dynamodb.dynamo_client import get_dynamodb_client
from src.infrastructure.dynamodb.mappers.conversation_mapper import ConversationMapper

class DynamoConversationRepositoryImpl(ConversationRepository):
    def __init__(self):
        self.client = get_dynamodb_client()
        self.table_name = "conversations"  # Set your actual DynamoDB table name here
        self.mapper = ConversationMapper()

    async def find_by_id_with_messages(self, id: str) -> Optional[Conversation]:
        item = await self.client.get_item(self.table_name, {"id": id})
        if not item:
            return None
        # Use mapper to convert DynamoDB dict to domain entity
        return self.mapper.to_entity(item)

    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        from boto3.dynamodb.conditions import Key
        key_condition = Key("user_id").eq(user_id)
        items = await self.client.query(
            table_name=self.table_name,
            key_condition_expression=key_condition,
            limit=limit
        )
        # Use mapper to convert each item to domain entity
        return [self.mapper.to_entity(item) for item in items]

    async def find_by_user_and_chatbot(self, user_id: str, chatbot_id: str) -> List[Conversation]:
        from boto3.dynamodb.conditions import Key, Attr
        key_condition = Key("user_id").eq(user_id)
        filter_expression = Attr("chatbot_id").eq(chatbot_id)
        items = await self.client.query(
            table_name=self.table_name,
            key_condition_expression=key_condition,
            filter_expression=filter_expression
        )
        # Use mapper to convert each item to domain entity
        return [self.mapper.to_entity(item) for item in items]
