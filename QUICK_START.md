# Quick Start Guide

## Complete Setup (5 Minutes)

### Step 1: Start Infrastructure (1 min)

```powershell
# Start Docker containers
docker-compose up -d localstack chromadb llm-service

# Verify they're running
docker ps
```

Expected output:
```
chatbot-localstack  (running)
chatbot-chromadb    (running)
chatbot-llm         (running)
```

### Step 2: Deploy System (2 min)

```powershell
# Deploy everything (Lambdas, EventBridge, S3 triggers)
.\scripts\deploy.ps1
```

Expected output:
```
✅ Deployed 3 Lambda functions
✅ EventBridge rules configured
✅ S3 event triggers configured
✅ 5 secrets configured
```

### Step 3: Configure API Keys (1 min)

```powershell
# Update with your real API keys
aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/voyage/api-key `
  --secret-string '{"api_key": "pa-YOUR-VOYAGE-API-KEY"}'

# For Slack (optional)
aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/slack/bot-token `
  --secret-string '{"bot_token": "xoxb-YOUR-SLACK-TOKEN"}'

# For GitLab (optional)
aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/gitlab/api-token `
  --secret-string '{"token": "glpat-YOUR-TOKEN", "base_url": "https://gitlab.com/api/v4/projects/123"}'

# For Backlog (optional)
aws --endpoint-url=http://localhost:4566 secretsmanager update-secret `
  --secret-id /chatbot/backlog/api-key `
  --secret-string '{"api_key": "YOUR-KEY", "space_url": "https://your-space.backlog.com"}'
```

### Step 4: Test the System (1 min)

```powershell
# Trigger data fetch manually
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-data-fetcher `
  response.json

# Check response
cat response.json
```

Expected response:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Data fetch and chunk completed",
    "total_documents": 50,
    "total_chunks": 150,
    "note": "Chunked data uploaded to S3. Embedder Lambda will be triggered automatically."
  }
}
```

### Step 5: Verify Embeddings (30 sec)

```powershell
# Wait a few seconds for embedder to process
Start-Sleep -Seconds 10

# Check ChromaDB
docker exec chatbot-app python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
try:
    collection = client.get_collection('chatbot_knowledge')
    print(f'✅ Total embeddings: {collection.count()}')
except:
    print('❌ No embeddings yet - check logs')
"
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│        EventBridge (Schedule: Every 6 hours)        │
└────────────────────┬────────────────────────────────┘
                     ↓
            ┌────────────────┐
            │ data_fetcher   │  ← Step 1: Fetch & Chunk
            │    Lambda      │
            └────────┬───────┘
                     ↓
            ┌────────────────┐
            │  S3 Bucket     │  ← Step 2: Store batches
            │  /chunked/     │
            └────────┬───────┘
                     ↓ (S3 Event Trigger)
            ┌────────────────┐
            │   embedder     │  ← Step 3: Embed chunks
            │    Lambda      │
            └────────┬───────┘
                     ↓
            ┌────────────────┐
            │   ChromaDB     │  ← Step 4: Vector store
            └────────────────┘
```

## Key Components

| Component | Purpose | Trigger |
|-----------|---------|---------|
| **data_fetcher Lambda** | Fetch from APIs, chunk data | EventBridge (6h) or Manual |
| **embedder Lambda** | Embed chunks into vectors | S3 Event (auto) |
| **S3 Bucket** | Store chunked data | N/A |
| **ChromaDB** | Vector database | N/A |

## Monitoring Commands

### Check Lambda Functions
```powershell
aws --endpoint-url=http://localhost:4566 lambda list-functions `
  --query 'Functions[?starts_with(FunctionName, `chatbot-`)].FunctionName'
```

### Check EventBridge Rules
```powershell
aws --endpoint-url=http://localhost:4566 events list-rules --name-prefix chatbot-
```

### Check S3 Trigger Configuration
```powershell
aws --endpoint-url=http://localhost:4566 s3api get-bucket-notification-configuration `
  --bucket chatbot-knowledge-base
```

### View Logs
```powershell
# Data fetcher logs
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-data-fetcher --follow

# Embedder logs
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --follow
```

### Check S3 Data
```powershell
# List chunked batches
aws --endpoint-url=http://localhost:4566 s3 ls `
  s3://chatbot-knowledge-base/ --recursive

# Count batch files
aws --endpoint-url=http://localhost:4566 s3 ls `
  s3://chatbot-knowledge-base/ --recursive | Select-String "batch_"
```

## Troubleshooting

### ❌ "No embeddings yet"

**Check 1: Did data_fetcher succeed?**
```powershell
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-data-fetcher --since 5m
```

**Check 2: Was S3 data created?**
```powershell
aws --endpoint-url=http://localhost:4566 s3 ls `
  s3://chatbot-knowledge-base/slack/chunked/ --recursive
```

**Check 3: Was embedder triggered?**
```powershell
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --since 5m
```

**Check 4: Is VoyageAI key valid?**
```powershell
aws --endpoint-url=http://localhost:4566 secretsmanager get-secret-value `
  --secret-id /chatbot/voyage/api-key
```

### ❌ "Lambda not found"

Re-deploy:
```powershell
.\scripts\deploy.ps1
```

### ❌ "S3 bucket not found"

Check LocalStack:
```powershell
docker logs chatbot-localstack --tail 50
```

Restart if needed:
```powershell
docker-compose restart localstack
.\scripts\deploy.ps1
```

## Manual Testing

### Test S3 Trigger Manually

1. Create test batch file:
```json
{
  "batch_id": "test_20251027_100000_abcd",
  "timestamp": "2025-10-27T10:00:00Z",
  "source": "test",
  "chunk_count": 2,
  "chunks": [
    {
      "text": "This is a test chunk about Python programming",
      "metadata": {"source": "test", "type": "test"}
    },
    {
      "text": "Another test chunk about machine learning",
      "metadata": {"source": "test", "type": "test"}
    }
  ]
}
```

2. Upload to S3:
```powershell
# Save above as test_batch.json
aws --endpoint-url=http://localhost:4566 s3 cp test_batch.json `
  s3://chatbot-knowledge-base/test/chunked/year=2025/month=10/day=27/batch_test.json
```

3. Check if embedder was triggered:
```powershell
aws --endpoint-url=http://localhost:4566 logs tail `
  /aws/lambda/chatbot-embedder --follow
```

### Test Embedder Directly

```powershell
# Use test S3 event
aws --endpoint-url=http://localhost:4566 lambda invoke `
  --function-name chatbot-embedder `
  --payload file://scripts/test_s3_event.json `
  response.json

cat response.json
```

## Production Checklist

Before going to production:

- [ ] Update all API keys in Secrets Manager
- [ ] Test with real data from each source (Slack, GitLab, Backlog)
- [ ] Verify embeddings are being created
- [ ] Set up monitoring/alerts
- [ ] Configure Dead Letter Queue for failed embeddings
- [ ] Test failure scenarios and retries
- [ ] Document any custom configurations
- [ ] Set up backup for ChromaDB data

## Getting Help

1. **Check logs first**: Most issues show up in Lambda logs
2. **Verify configuration**: Ensure all secrets are set correctly
3. **Test components individually**: Isolate which component is failing
4. **Review architecture**: See [EMBEDDING_ARCHITECTURE.md](EMBEDDING_ARCHITECTURE.md)
5. **Deployment issues**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## Next Steps

- Configure automatic scheduling (EventBridge already set to 6 hours)
- Add more data sources (Discord, Excel files)
- Monitor embedding quality
- Set up production monitoring
- Scale based on data volume

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy | `.\scripts\deploy.ps1` |
| Fetch data | `aws lambda invoke --function-name chatbot-data-fetcher response.json` |
| Check embeddings | `docker exec chatbot-app python -c "import chromadb..."` |
| View logs | `aws logs tail /aws/lambda/chatbot-data-fetcher --follow` |
| List S3 data | `aws s3 ls s3://chatbot-knowledge-base/ --recursive` |

**System is ready! Data will be automatically fetched and embedded every 6 hours.** 🚀
