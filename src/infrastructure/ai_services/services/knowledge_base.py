"""
AWS Bedrock Knowledge Base Service.
"""

from shared.interfaces.services.ai_services.knowledge_base_service import IKnowledgeBaseService
from infrastructure.ai_services.providers.bedrock import BedrockClient
from typing import List, Dict, Any

class BedrockKnowledgeBaseService(IKnowledgeBaseService):
    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock_client = bedrock_client
        self.domain_kb_mapping = {
            "healthcare": "KB_HEALTHCARE_ID",
            "education": "KB_EDUCATION_ID", 
            "finance": "KB_FINANCE_ID",
            "general": "KB_GENERAL_ID"
        }
    
    async def retrieve_contexts(self, query: str, knowledge_base_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        response = await self.bedrock_client.invoke_bedrock_agent(
            input_text=query,
            knowledge_base_id=knowledge_base_id,
            number_of_results=top_k
        )
        
        contexts = []
        for result in response.get("retrievalResults", []):
            context = {
                "text": result.get("content", {}).get("text", ""),
                "source": result.get("location", {}).get("s3Location", {}).get("uri", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            }
            contexts.append(context)
        
        return contexts
    
    async def get_knowledge_base_by_domain(self, domain: str) -> str:
        kb_id = self.domain_kb_mapping.get(domain, self.domain_kb_mapping["general"])
        return kb_id