"""
Shared Bedrock client used by LLM, Embeddings, and other services.

Placed at infrastructure.ai_services to keep a clear dependency boundary
between providers and a single location for low-level Bedrock access.
"""
from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from core.config import settings


class BedrockClient:
    """Client wrapper for AWS Bedrock runtime APIs.

    This class is intentionally minimal and kept in a single module so other
    provider implementations (LLM, Embeddings, KB) can import it without
    importing provider modules and creating circular dependencies.
    """

    def __init__(self, region: Optional[str] = None):
        region = region or settings.BEDROCK_REGION
        config = Config(region_name=region)
        # boto3 client for Bedrock runtime
        self.client = boto3.client('bedrock-runtime', config=config)
        # boto3 client for Bedrock Agent runtime (for Knowledge Bases)
        self.agent_runtime = boto3.client('bedrock-agent-runtime', config=config)

    def invoke_model(self, modelId: str, input: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a Bedrock model and return the raw response."""
        response = self.client.invoke_model(
            modelId=modelId,
            contentType='application/json',
            accept='application/json',
            body=input
        )
        return response

    async def invoke_bedrock_agent(
        self,
        input_text: str,
        knowledge_base_id: str,
        model_arn: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent Runtime for Knowledge Base queries.

        Args:
            input_text: Query text
            knowledge_base_id: ID of the Knowledge Base to query
            model_arn: Optional model ARN (defaults to configured model)
            **kwargs: Additional parameters

        Returns:
            Dict containing the response from Knowledge Base
        """
        try:
            response = self.agent_runtime.retrieve_and_generate(
                input={
                    'text': input_text
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': model_arn or kwargs.get('model_arn', settings.BEDROCK_MODEL_ID)
                    }
                }
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Error invoking Bedrock Knowledge Base: {e}")


def get_bedrock_client() -> BedrockClient:
    """Factory helper used by dependency injection.

    Returns a fresh BedrockClient instance. If you prefer a singleton or
    session-scoped client, replace this with the desired lifecycle.
    """
    return BedrockClient()
