# Automatic Data Fetching & Embedding System

## Overview

This system automatically fetches data from multiple sources (Slack, GitLab, Backlog, Discord) and embeds them into ChromaDB for RAG-based chatbot queries.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     EventBridge Scheduler                    │
│  (Cronjobs run every 6 hours)                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────┴──────────────────┐
        │                                      │
        ▼                                      ▼
┌───────────────┐                    ┌───────────────┐
│ Data Fetcher  │                    │Discord Fetcher│
│   Lambda      │                    │   Lambda      │
│               │                    └───────────────┘
│ • Fetch APIs  │
│ • Chunk Data  │
│ • Embed       │
│ • Store       │
└───────┬───────┘
        │
        ├──────────► (Optional) S3 Bucket (Backup)
        │
        ▼
┌──────────────────┐
│ Chunk Router     │
│ (Smart Chunking) │
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│ VoyageAI         │
│ (Embeddings)     │
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│   ChromaDB       │
│ (Vector Store)   │
└──────────────────┘
```

## Components

### 1. Lambda Functions

#### data_fetcher (All-in-One)
- **Purpose**: Fetch, chunk, embed, and store data from Slack, GitLab, and Backlog
- **Schedule**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **Flow**:
  1. Fetch data from APIs
  2. Transform to document format
  3. (Optional) Save to S3 for backup
  4. Chunk documents using smart routing
  5. Embed with VoyageAI
  6. Store in ChromaDB
- **Configuration**:
  - `embed_immediately`: true/false (default: true)
  - `skip_s3`: true/false (default: false)
- **Location**: `lambda/data_fetcher/lambda_function.py`

#### discord_fetcher
- **Purpose**: Fetch messages and threads from Discord
- **Schedule**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- **Output**: Raw JSON documents in S3
- **Location**: `lambda/discord_fetcher/lambda_function.py`
- **Note**: Can be integrated with chunking/embedding like data_fetcher

### 2. Chunking Router

Smart chunking strategy based on data source type:

- **Slack/Discord**: Conversation window chunks (10 messages, 2 overlap)
- **Code**: Function/class boundary chunks
- **Markdown**: Header-based chunks
- **Issues/Backlog**: Issue + comments chunks
- **Excel**: Row-level + sheet summary chunks
- **Git**: Commit/PR with diff chunks

**Location**: `app/embeddings/chunk_router.py`

### 3. EventBridge Rules

Automated scheduling for Lambda execution:

| Rule Name | Schedule | Description |
|-----------|----------|-------------|
| chatbot-data-fetcher-schedule | Every 6 hours | Fetch, chunk, embed Slack, GitLab, Backlog |
| chatbot-discord-fetcher-schedule | Every 6 hours | Fetch Discord data |

## Setup & Deployment

### Prerequisites

- Docker & Docker Compose running
- LocalStack container
- ChromaDB container
- Python 3.11+
- AWS CLI configured

### Quick Start

1. **Deploy full system**:
   ```powershell
   .\scripts\deploy_full_system.ps1
   ```

2. **Update API tokens in Secrets Manager**:
   ```powershell
   # Slack
   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
     --secret-id /chatbot/slack/bot-token `
     --secret-string '{"bot_token": "xoxb-your-real-token"}'

   # GitLab
   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
     --secret-id /chatbot/gitlab/api-token `
     --secret-string '{"token": "glpat-xxx", "base_url": "https://gitlab.com/api/v4/projects/123"}'

   # Backlog
   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
     --secret-id /chatbot/backlog/api-key `
     --secret-string '{"api_key": "xxx", "space_url": "https://your-space.backlog.com"}'

   # Discord
   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
     --secret-id /chatbot/discord/bot-token `
     --secret-string '{"bot_token": "MTxxx", "guild_id": "123", "channel_ids": "456,789"}'

   # VoyageAI
   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
     --secret-id /chatbot/voyage/api-key `
     --secret-string '{"api_key": "pa-xxx"}'
   ```

3. **Verify deployment**:
   ```powershell
   # Check Lambda functions
   aws --endpoint-url=http://localhost:4566 lambda list-functions

   # Check EventBridge rules
   aws --endpoint-url=http://localhost:4566 events list-rules --name-prefix "chatbot-"
   ```

### Manual Deployment Steps

If you prefer step-by-step deployment:

1. **Deploy Lambda functions only**:
   ```powershell
   python scripts\deploy_lambdas.py
   ```

2. **Setup EventBridge cronjobs**:
   ```powershell
   python scripts\setup_eventbridge_cronjobs.py
   ```

## Usage

### Manual Trigger

#### Trigger Data Fetch & Embedding
```powershell
# Fetch and embed immediately (default)
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  response.json

# Fetch only, skip embedding
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  --payload '{"embed_immediately": false}' `
  response.json

# Fetch and embed, skip S3 backup
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  --payload '{"embed_immediately": true, "skip_s3": true}' `
  response.json

# Check response
cat response.json
```

### Monitor Execution

#### Check S3 Data
```powershell
# List all fetched data
aws --endpoint-url=http://localhost:4566 s3 ls s3://chatbot-knowledge-base/ --recursive

# List Slack data
aws --endpoint-url=http://localhost:4566 s3 ls s3://chatbot-knowledge-base/slack/

# Download a document
aws --endpoint-url=http://localhost:4566 s3 cp `
  s3://chatbot-knowledge-base/slack/year=2025/month=10/day=27/20251027_100000_doc_0.json `
  .
```

#### Check Lambda Logs
```powershell
# Tail logs in real-time
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-data-fetcher --follow

aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --follow
```

#### Check ChromaDB
```powershell
# Via Docker
docker exec chatbot-app python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('chatbot_knowledge')
print(f'Total documents: {collection.count()}')
"
```

### Manage Cronjobs

#### Disable a cronjob
```powershell
aws --endpoint-url=http://localhost:4566 events disable-rule `
  --name chatbot-data-fetcher-schedule
```

#### Enable a cronjob
```powershell
aws --endpoint-url=http://localhost:4566 events enable-rule `
  --name chatbot-data-fetcher-schedule
```

#### Update schedule
```powershell
# Change to run every 12 hours
aws --endpoint-url=http://localhost:4566 events put-rule `
  --name chatbot-data-fetcher-schedule `
  --schedule-expression "rate(12 hours)"
```

## Configuration

### Environment Variables

Set these in Lambda function configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| S3_BUCKET_NAME | S3 bucket for raw data | chatbot-knowledge-base |
| CHROMADB_HOST | ChromaDB host | chromadb |
| CHROMADB_PORT | ChromaDB port | 8000 |
| VOYAGE_API_KEY | VoyageAI API key | From Secrets Manager |

### Chunking Parameters

Customize chunking in `app/embeddings/chunk_router.py`:

```python
# Slack window size
chunk_slack(messages, window_size=10, overlap=2)

# Code chunk size
RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

# Excel chunk size
RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
```

### Embedding Batch Size

Adjust in `lambda/data_fetcher/lambda_function.py`:

```python
batch_size = 50  # Number of documents per batch
# Adjust based on VoyageAI rate limits
```

## Troubleshooting

### Issue: Lambda timeout
**Solution**: Increase timeout in `scripts/deploy_lambdas.py`:
```python
"timeout": 900,  # 15 minutes
"memory_size": 1024  # 1GB
```

### Issue: VoyageAI rate limit
**Solution**: Add delay between batches in data_fetcher Lambda:
```python
import time
time.sleep(20)  # Wait 20 seconds between batches
```

### Issue: ChromaDB connection error
**Solution**: Check ChromaDB is running:
```powershell
docker ps | grep chromadb
docker logs chatbot-chromadb
```

### Issue: Empty S3 bucket
**Solution**: Manually trigger data fetcher and check logs:
```powershell
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  --log-type Tail `
  response.json
```

## File Structure

```
kass/
├── lambda/
│   ├── data_fetcher/          # Fetch, chunk, embed (all-in-one)
│   │   ├── lambda_function.py # Main Lambda with integrated embedding
│   │   └── requirements.txt   # Dependencies
│   └── discord_fetcher/       # Fetch Discord
├── app/
│   └── embeddings/
│       ├── chunk_router.py    # Smart chunking logic
│       ├── voyage_client.py   # VoyageAI client
│       └── base.py            # Base interfaces
├── scripts/
│   ├── deploy_lambdas.py      # Deploy all Lambdas
│   ├── setup_eventbridge_cronjobs.py  # Setup cronjobs
│   ├── deploy_full_system.ps1 # Full deployment script
│   └── manual_trigger.json    # Manual trigger config
└── EMBEDDING_SYSTEM_README.md # This file
```

## Best Practices

1. **Rate Limits**: Always respect API rate limits
   - VoyageAI free tier: 3 RPM
   - Add delays between batches
   - Monitor usage

2. **Error Handling**: Lambdas continue on errors
   - Check logs regularly
   - Set up CloudWatch alarms (for production)
   - Retry failed batches

3. **Data Freshness**: Schedule based on update frequency
   - High-traffic Slack: Every 3-6 hours
   - Low-traffic GitLab: Every 12 hours
   - Adjust as needed

4. **Storage**: Clean up old S3 data periodically
   - Set lifecycle policies
   - Archive old data to Glacier
   - Keep last 30 days in S3

5. **Monitoring**: Track metrics
   - Documents fetched per run
   - Embeddings created per run
   - ChromaDB collection size
   - Lambda execution time

## Future Enhancements

- [ ] Add incremental updates (only fetch new data)
- [ ] Add data deduplication
- [ ] Add embedding quality metrics
- [ ] Add Slack channel filtering
- [ ] Add GitLab project filtering
- [ ] Add retry logic for failed embeddings
- [ ] Add notification on errors (SNS/Slack)
- [ ] Add dashboard for monitoring (Grafana)

## Support

For issues or questions:
- Check logs: `aws logs tail /aws/lambda/chatbot-*`
- Review EventBridge: `aws events list-rules`
- Check S3: `aws s3 ls s3://chatbot-knowledge-base/`
