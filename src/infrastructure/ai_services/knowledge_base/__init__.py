"""
Knowledge Base services for RAG (Retrieval-Augmented Generation).
"""

# Optional Bedrock support (requires boto3)
try:
    from infrastructure.ai_services.knowledge_base.bedrock_kb import BedrockKnowledgeBaseService
    _BEDROCK_AVAILABLE = True
except ImportError:
    BedrockKnowledgeBaseService = None
    _BEDROCK_AVAILABLE = False

__all__ = ["BedrockKnowledgeBaseService"]
