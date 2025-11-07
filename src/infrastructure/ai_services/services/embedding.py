"""
AWS Bedrock Embedding Service.
"""

from shared.interfaces.services.ai_services.embedding_service import IEmbeddingService
from infrastructure.ai_services.providers.bedrock import BedrockClient
from typing import List
import asyncio

class BedrockEmbeddingService(IEmbeddingService):
    def __init__(self, bedrock_client: BedrockClient, model_id: str = "amazon.titan-embed-text-v1"):
        self.bedrock_client = bedrock_client
        self.model_id = model_id
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        tasks = [self.create_single_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def create_single_embedding(self, text: str) -> List[float]:
        response = await self.bedrock_client.invoke_model(
            model_id=self.model_id,
            body={"inputText": text}
        )
        return response.get("embedding", [])