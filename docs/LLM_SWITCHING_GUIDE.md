# LLM Service Switching Example

Hệ thống LLM hiện tại hỗ trợ switching linh hoạt giữa AWS Bedrock và Google Gemini.

## Cấu hình

### Environment Variables
```bash
# LLM Provider (bedrock hoặc gemini)
LLM_PROVIDER=bedrock

# AWS Bedrock
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini-1.5-pro
```

## API Endpoints

### 1. Xem thông tin LLM hiện tại
```bash
GET /api/v1/llm/current
```

### 2. Xem tất cả providers có sẵn
```bash
GET /api/v1/llm/providers
```

### 3. Test LLM provider
```bash
POST /api/v1/llm/test
{
  "prompt": "Xin chào, bạn có thể giúp tôi không?",
  "provider": "gemini",
  "model_id": "gemini-1.5-pro",
  "max_tokens": 100,
  "temperature": 0.7
}
```

### 4. Switch LLM provider (temporary)
```bash
POST /api/v1/llm/switch
{
  "provider": "gemini",
  "model_id": "gemini-1.5-pro"
}
```

### 5. RAG với LLM provider hiện tại
```bash
POST /api/v1/rag/chat
{
  "query": "Tôi muốn biết về sản phẩm ABC",
  "domain": "products",
  "context_limit": 5
}
```

### 6. Xem thông tin RAG system
```bash
GET /api/v1/rag/info
```

## Cách sử dụng trong code

### Sử dụng factory pattern với RAG Service
```python
from src.infrastructure.ai_services.factory import LLMFactory
from src.application.services.rag_service import RAGService
from src.infrastructure.ai_services.services.knowledge_base import BedrockKnowledgeBaseService

# Tạo LLM provider
bedrock_llm = LLMFactory.create("bedrock", "anthropic.claude-3-sonnet-20240229-v1:0")
gemini_llm = LLMFactory.create("gemini", "gemini-1.5-pro")

# Tạo RAG service với LLM provider
knowledge_base_service = BedrockKnowledgeBaseService(bedrock_client)
rag_service = RAGService(knowledge_base_service, bedrock_llm)

# Sử dụng cho RAG
response = await rag_service.chat_with_documents("What is this document about?", domain="general")

# Sử dụng cho direct LLM
response = await rag_service.generate_response("Hello!")
```

### Sử dụng dependency injection
```python
from src.core.dependencies import get_rag_service

@app.post("/my-endpoint")
async def my_endpoint(
    rag_service: IRAGService = Depends(get_rag_service)
):
    # RAG functionality
    rag_response = await rag_service.chat_with_documents("Query", domain="general")
    
    # Direct LLM functionality  
    llm_response = await rag_service.generate_response("Hello!")
    
    return {
        "rag_response": rag_response,
        "llm_response": llm_response, 
        "provider": rag_service.get_provider_name()
    }
```

## Lợi ích

1. **Flexibility**: Dễ dàng switch giữa các LLM providers
2. **Consistency**: Interface thống nhất cho tất cả providers
3. **Testing**: Có thể test các providers khác nhau
4. **Fallback**: Có thể implement fallback strategy
5. **Local Development**: Sử dụng Gemini cho dev, Bedrock cho production

## Architecture

```
RAG Service
    ↓
LLM Service (Interface)
    ↓
LLM Factory
    ↓
┌─────────────┬─────────────┐
│ Bedrock LLM │ Gemini LLM  │
│             │             │
│ • Bedrock   │ • Google    │
│   Client    │   Gemini    │
│ • Knowledge │   API       │
│   Base      │             │
│ • Embedding │             │
└─────────────┴─────────────┘

All LLM providers are consolidated in:
src/infrastructure/llm/
├── base.py                     # Abstract base class
├── factory.py                  # Factory pattern
├── bedrock_llm.py             # AWS Bedrock LLM
├── gemini_llm.py              # Google Gemini LLM
├── bedrock_client.py          # AWS Bedrock client
├── knowledge_base_service_impl.py # Bedrock KB service
└── embedding_service_impl.py  # Bedrock embedding service
```

## Cách thêm LLM provider mới

1. Tạo class implement `BaseLLMService`
2. Thêm vào `LLMFactory.create()`
3. Thêm config trong `settings`
4. Update `get_available_providers()` và `get_provider_models()`