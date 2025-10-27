# Deployment Guide

## Quick Start (3 Steps)

### 1. Start Infrastructure

```powershell
# Start Docker services
docker-compose up -d localstack chromadb llm-service
```

### 2. Deploy Everything

```powershell
# Deploy all Lambda functions, EventBridge, S3 triggers, and secrets
.\scripts\deploy.ps1
```

### 3. Update API Tokens

```powershell
# Update with your real tokens
aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/slack/bot-token `
  --secret-string '{"bot_token": "xoxb-YOUR-REAL-TOKEN"}'

aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/voyage/api-key `
  --secret-string '{"api_key": "pa-YOUR-REAL-KEY"}'
```

## What Gets Deployed

| Component | Description |
|-----------|-------------|
| **3 Lambda Functions** | data_fetcher, discord_fetcher, embedder |
| **2 EventBridge Rules** | Scheduled fetch every 6 hours |
| **S3 Bucket** | Storage for chunked data |
| **S3 Event Trigger** | Auto-triggers embedder on new data |
| **5 Secrets** | API tokens in Secrets Manager |

## Architecture

```
EventBridge → data_fetcher → S3 → embedder → ChromaDB
   (6h)      (fetch+chunk)   (trigger) (embed)  (store)
```

## Manual Operations

### Trigger Data Fetch

```powershell
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  response.json

cat response.json
```

### Check Logs

```powershell
# Data fetcher
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-data-fetcher --follow

# Embedder
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --follow
```

### Check S3 Data

```powershell
aws --endpoint-url=http://localhost:4566 s3 ls `
  s3://chatbot-knowledge-base/ --recursive
```

### Check ChromaDB

```powershell
docker exec chatbot-app python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('chatbot_knowledge')
print(f'Total embeddings: {collection.count()}')
"
```

## Configuration

All configuration is in `scripts/deploy.py`:

- Lambda function settings (timeout, memory)
- EventBridge schedules
- S3 bucket name
- Default secrets

## Troubleshooting

### Deployment fails

```powershell
# Check LocalStack is running
docker ps | grep localstack

# Check Python dependencies
pip install boto3

# Re-run deployment
.\scripts\deploy.ps1
```

### Lambda not triggered

```powershell
# Verify EventBridge rule
aws --endpoint-url=http://localhost:4566 events list-rules --name-prefix chatbot-

# Verify S3 notification
aws --endpoint-url=http://localhost:4566 s3api get-bucket-notification-configuration `
  --bucket chatbot-knowledge-base
```

### Embedder not working

```powershell
# Check VoyageAI key
aws --endpoint-url=http://localhost:4566 secretsmanager get-secret-value `
  --secret-id /chatbot/voyage/api-key

# Test embedder manually
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-embedder `
  --payload file://scripts/test_s3_event.json `
  response.json
```

## Old Scripts (Deprecated)

These scripts are replaced by `deploy.py`:

- ❌ `deploy_lambdas.py` → Use `deploy.py`
- ❌ `setup_eventbridge_cronjobs.py` → Use `deploy.py`
- ❌ `setup_s3_triggers.py` → Use `deploy.py`
- ❌ `deploy_full_system.ps1` → Use `deploy.ps1`

Other scripts still useful:

- ✅ `embed_via_api.py` - Manual embedding from Excel
- ✅ `run_data_fetcher.py` - Quick local testing

## Advanced

### Deploy Only Lambdas

```python
# Edit deploy.py, comment out sections:
# setup_eventbridge()
# setup_s3()
# setup_secrets()
```

### Change Schedule

```python
# In deploy.py, update:
"schedule": "rate(12 hours)"  # Instead of 6 hours
```

### Add New Lambda

```python
# In deploy.py, add to LAMBDA_FUNCTIONS list:
{
    "name": "my_lambda",
    "handler": "lambda_function.lambda_handler",
    "runtime": "python3.11",
    "description": "My custom Lambda",
    "timeout": 300,
    "memory_size": 512,
    "env": {"MY_VAR": "value"}
}
```

## Files

```
scripts/
├── deploy.py          # ⭐ Unified deployment (Python)
├── deploy.ps1         # ⭐ Simple wrapper (PowerShell)
├── test_s3_event.json # Test S3 event payload
├── embed_via_api.py   # Manual Excel embedding
└── run_data_fetcher.py # Local testing
```

## Support

- Architecture details: See [EMBEDDING_ARCHITECTURE.md](../EMBEDDING_ARCHITECTURE.md)
- Issues: Check logs first, then review architecture doc
