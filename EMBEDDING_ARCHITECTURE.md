# Event-Driven Embedding Architecture

## Overview

This system uses an **event-driven architecture** where data fetching and embedding are decoupled via S3 events. This provides better scalability, fault tolerance, and separation of concerns.

## Architecture Flow

```
┌─────────────────────────────────────────────────────┐
│            EventBridge Scheduler                     │
│        (Every 6 hours: 00:00, 06:00, 12:00, 18:00)  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │  Data Fetcher    │
        │     Lambda       │
        │                  │
        │ • Fetch APIs     │
        │ • Transform      │
        │ • Chunk data     │
        └────────┬─────────┘
                 │
                 ▼
         ┌───────────────┐
         │  S3 Bucket    │
         │ */chunked/    │
         │ batch_*.json  │
         └───────┬───────┘
                 │
                 │ S3 Event Trigger
                 │ (ObjectCreated:*)
                 ▼
         ┌───────────────┐
         │  Embedder     │
         │    Lambda     │
         │               │
         │ • Load chunks │
         │ • Embed       │
         │ • Store       │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │  ChromaDB     │
         │ Vector Store  │
         └───────────────┘
```

## Why Event-Driven?

### Benefits

1. **Decoupling**: Fetch and embed are independent, can scale separately
2. **Fault Tolerance**: If embedding fails, S3 data persists for retry
3. **Observability**: Each step has clear boundaries and logs
4. **Cost Optimization**: Pay only when processing data (not polling)
5. **Flexibility**: Easy to add more consumers (e.g., backup, analytics)

### Comparison with Previous Approach

| Aspect | Old (Inline) | New (Event-Driven) |
|--------|-------------|-------------------|
| Coupling | Tight | Loose |
| Retry | Restart entire process | Retry only embedding |
| Scaling | Limited by single Lambda | Independent scaling |
| Observability | Single log stream | Multiple log streams |
| S3 Backup | Optional | Always persisted |

## Components

### 1. Data Fetcher Lambda

**Responsibility**: Fetch data from APIs and prepare for embedding

- **Triggers**: EventBridge (scheduled)
- **Actions**:
  1. Fetch from Slack, GitLab, Backlog APIs
  2. Transform to standard document format
  3. Chunk using smart routing (conversation windows, code blocks, etc.)
  4. Save chunked data to S3 as batch files
- **Output**: `s3://bucket/{source}/chunked/year=*/month=*/day=*/batch_{id}.json`
- **Timeout**: 5 minutes
- **Memory**: 512MB

**Batch File Format**:
```json
{
  "batch_id": "20251027_100000_a1b2",
  "timestamp": "2025-10-27T10:00:00Z",
  "source": "slack",
  "chunk_count": 150,
  "chunks": [
    {
      "text": "User1: How do we handle errors?\nUser2: Check the docs...",
      "metadata": {
        "source": "slack",
        "channel": "dev-team",
        "start_time": "2025-10-27T09:00:00Z",
        "message_count": 10
      }
    }
  ]
}
```

### 2. S3 Event Trigger

**Responsibility**: Automatically invoke embedder when new data arrives

- **Event**: `s3:ObjectCreated:*`
- **Filter**:
  - Prefix: `*/chunked/`
  - Suffix: `.json`
- **Target**: Embedder Lambda
- **Configuration**: Managed via `setup_s3_triggers.py`

### 3. Embedder Lambda

**Responsibility**: Embed chunks and store in vector database

- **Triggers**: S3 event notifications
- **Actions**:
  1. Receive S3 event with object key
  2. Download batch file from S3
  3. Embed chunks using VoyageAI (or alternative)
  4. Store embeddings in ChromaDB
- **Timeout**: 15 minutes
- **Memory**: 1GB
- **Rate Limiting**: Handles VoyageAI 3 RPM limit

## Embedding Alternatives (No Bedrock)

Since AWS Bedrock is not used, here are alternative embedding solutions:

### Option 1: VoyageAI (Current Implementation) ✅
```python
from embeddings.voyage_client import VoyageEmbeddingProvider

voyage = VoyageEmbeddingProvider()
embeddings = await voyage.embed_texts(texts)
```

**Pros**:
- High quality embeddings
- Specialized models (voyage-2, voyage-code-2)
- Good documentation

**Cons**:
- Free tier limited (3 RPM)
- External dependency

### Option 2: OpenAI API
```python
import openai

response = openai.Embedding.create(
    input=texts,
    model="text-embedding-3-small"
)
embeddings = [d['embedding'] for d in response['data']]
```

**Pros**:
- Reliable, mature API
- Multiple model sizes

**Cons**:
- Cost ($0.02 per 1M tokens)
- Rate limits

### Option 3: Cohere API
```python
import cohere

co = cohere.Client(api_key)
response = co.embed(texts=texts, model='embed-english-v3.0')
embeddings = response.embeddings
```

**Pros**:
- Good quality
- Multilingual support

**Cons**:
- Pricing
- Rate limits

### Option 4: HuggingFace Inference API
```python
import requests

headers = {"Authorization": f"Bearer {api_key}"}
response = requests.post(
    "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
    headers=headers,
    json={"inputs": texts}
)
embeddings = response.json()
```

**Pros**:
- Free tier available
- Many models to choose from

**Cons**:
- Cold start delays
- May need model selection

### Option 5: Self-Hosted (sentence-transformers) 🚀
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)
```

**Pros**:
- No API costs
- No rate limits
- Full control

**Cons**:
- Need to host model
- Lambda size limits (need EFS or container)

**Recommended for production**: Use AWS Lambda with EFS to mount model files

## Deployment

### Quick Start

```powershell
# Deploy entire system
.\scripts\deploy_full_system.ps1
```

This will:
1. Deploy all Lambda functions (data_fetcher, discord_fetcher, embedder)
2. Setup EventBridge schedules
3. Configure S3 event notifications
4. Create secrets and S3 bucket

### Manual Steps

```powershell
# 1. Deploy Lambdas
python scripts\deploy_lambdas.py

# 2. Setup EventBridge
python scripts\setup_eventbridge_cronjobs.py

# 3. Setup S3 Triggers
python scripts\setup_s3_triggers.py
```

## Usage

### Trigger Data Fetch

```powershell
# Manually trigger data fetcher
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  response.json

# This will:
# 1. Fetch data from APIs
# 2. Chunk data
# 3. Save to S3
# 4. Automatically trigger embedder via S3 event
```

### Monitor Processing

```powershell
# Check S3 for chunked data
aws --endpoint-url=http://localhost:4566 s3 ls `
  s3://chatbot-knowledge-base/slack/chunked/ --recursive

# Check data fetcher logs
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-data-fetcher --follow

# Check embedder logs
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --follow

# Check ChromaDB
docker exec chatbot-app python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('chatbot_knowledge')
print(f'Total embeddings: {collection.count()}')
"
```

### Test S3 Trigger

```powershell
# Test embedder with sample S3 event
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-embedder `
  --payload file://scripts/test_s3_event.json `
  response.json

cat response.json
```

## Configuration

### Environment Variables

#### Data Fetcher Lambda
- `S3_BUCKET_NAME`: S3 bucket for chunked data

#### Embedder Lambda
- `CHROMADB_HOST`: ChromaDB host (default: chromadb)
- `CHROMADB_PORT`: ChromaDB port (default: 8000)
- `VOYAGE_API_KEY`: From Secrets Manager

### S3 Bucket Structure

```
chatbot-knowledge-base/
├── slack/
│   └── chunked/
│       └── year=2025/
│           └── month=10/
│               └── day=27/
│                   ├── batch_20251027_100000_a1b2.json
│                   └── batch_20251027_160000_c3d4.json
├── gitlab/
│   └── chunked/...
└── backlog/
    └── chunked/...
```

## Monitoring & Troubleshooting

### Check S3 Event Configuration

```powershell
aws --endpoint-url=http://localhost:4566 s3api get-bucket-notification-configuration `
  --bucket chatbot-knowledge-base
```

### Common Issues

#### Issue: Embedder not triggered
**Solution**: Check S3 notification configuration
```powershell
python scripts\setup_s3_triggers.py
```

#### Issue: VoyageAI rate limit
**Solution**: Embedder already handles this with batching and delays
- Check logs for retry messages
- Consider upgrading VoyageAI tier

#### Issue: ChromaDB connection failed
**Solution**: Ensure ChromaDB is running
```powershell
docker ps | grep chromadb
docker logs chatbot-chromadb
```

#### Issue: S3 event not received
**Solution**: Check Lambda permissions
```powershell
aws --endpoint-url=http://localhost:4566 lambda get-policy `
  --function-name chatbot-embedder
```

## Performance Optimization

### Batch Size Tuning

**Data Fetcher** (`lambda/data_fetcher/lambda_function.py:390`):
```python
# All chunks in single batch file
# Adjust based on API data volume
```

**Embedder** (`lambda/embedder/lambda_function.py:56`):
```python
batch_size = 50  # Embeddings per request
# Balance between throughput and rate limits
```

### Retry Strategy

S3 events automatically retry failed invocations:
- Up to 2 retries
- Failed events go to Dead Letter Queue (if configured)
- Batch files persist in S3 for manual reprocessing

## Cost Estimation

### VoyageAI Free Tier
- 3 requests per minute
- ~150 chunks per batch
- ~3 batches per hour max
- **Cost**: Free

### Paid Tier Recommendation
For production with higher volume:
- VoyageAI: $0.12 per 1M tokens
- OpenAI: $0.02 per 1M tokens (text-embedding-3-small)
- Self-hosted: Infrastructure cost only

## Future Enhancements

- [ ] Dead Letter Queue for failed embeddings
- [ ] Batch reprocessing endpoint
- [ ] Multiple embedding providers (fallback)
- [ ] Embedding quality metrics
- [ ] Incremental updates (only new data)
- [ ] Compression for S3 batch files
- [ ] CloudWatch dashboards
- [ ] SNS notifications on failures

## File Structure

```
kass/
├── lambda/
│   ├── data_fetcher/        # Fetch + chunk
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── discord_fetcher/     # Discord fetch
│   └── embedder/            # Embed (S3 triggered)
│       ├── lambda_function.py
│       └── requirements.txt
├── app/
│   └── embeddings/
│       ├── chunk_router.py  # Smart chunking
│       ├── voyage_client.py # VoyageAI client
│       └── base.py
├── scripts/
│   ├── deploy_lambdas.py
│   ├── setup_eventbridge_cronjobs.py
│   ├── setup_s3_triggers.py      # 🆕 S3 event setup
│   ├── test_s3_event.json        # 🆕 Test event
│   └── deploy_full_system.ps1
└── EMBEDDING_ARCHITECTURE.md     # This file
```

## Support

For issues:
- Check logs: `aws logs tail /aws/lambda/chatbot-*`
- Verify S3 events: `aws s3api get-bucket-notification-configuration`
- Test manually: `aws lambda invoke --payload file://test_s3_event.json`
