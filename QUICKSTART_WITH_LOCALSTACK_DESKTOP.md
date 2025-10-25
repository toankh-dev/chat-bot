# 🚀 Quick Start Guide - LocalStack Desktop Version

## ✅ Prerequisites

- ✅ LocalStack Desktop installed
- ✅ Docker Desktop installed và đang chạy
- ✅ Auth key: `ls-siWACAyO-9014-qeMI-3043-qojItIhide54`
- 16GB+ RAM
- 50GB+ disk space

---

## 📋 Step-by-Step Setup

### Step 1: Start LocalStack Desktop

1. **Mở LocalStack Desktop app**
2. **Click "Start LocalStack"**
3. **Verify đang running** - Status hiển thị màu xanh
4. **Check port 4566** - Phải available

![LocalStack Desktop Running](https://via.placeholder.com/600x200?text=LocalStack+Desktop+Running)

### Step 2: Verify LocalStack is Running

```bash
# Test connection
curl http://localhost:4566/_localstack/health

# Expected output:
{
  "services": {
    "s3": "running",
    "dynamodb": "running",
    "secretsmanager": "running"
  }
}
```

✅ Nếu thấy response trên → LocalStack OK!

### Step 3: Update .env File

File `.env` đã được tạo với auth key của bạn. **CHỈ CẦN thêm API keys**:

```bash
# Edit .env file
notepad .env

# Tìm và thay đổi:
GITLAB_TOKEN=glpat-YOUR-GITLAB-TOKEN-HERE
SLACK_BOT_TOKEN=xoxb-YOUR-SLACK-BOT-TOKEN-HERE
BACKLOG_API_KEY=YOUR-BACKLOG-API-KEY-HERE
BACKLOG_SPACE_URL=https://your-space.backlog.com
```

**LocalStack auth key đã có sẵn rồi!** ✅

### Step 4: Comment LocalStack Service trong docker-compose.yml

```yaml
# Edit docker-compose.yml
# Tìm phần localstack và comment lại:

services:
  # LocalStack - USING DESKTOP APP, SO COMMENT THIS OUT
  # localstack:
  #   image: localstack/localstack-pro:latest
  #   container_name: chatbot-localstack
  #   ports:
  #     - "4566:4566"
  #   ...

  # ChromaDB - KEEP THIS
  chromadb:
    image: chromadb/chroma:latest
    ...
```

**Hoặc đơn giản hơn**: Khi start services, bỏ qua localstack:

```bash
# Start chỉ các services cần thiết (không có localstack)
docker-compose up -d chromadb embedding-service llm-service postgres redis app
```

### Step 5: Start Docker Services

```bash
# Navigate to project directory
cd c:\Users\toankh\Documents\chat-bot

# Start services (KHÔNG bao gồm localstack vì đã dùng Desktop)
docker-compose up -d chromadb embedding-service llm-service postgres redis app
```

**Services starting:**
- ✅ ChromaDB (vector database)
- ✅ Embedding Service (downloading model ~500MB)
- ✅ LLM Service (downloading model ~14GB) ⏳ **Mất 10-30 phút**
- ✅ PostgreSQL (database)
- ✅ Redis (cache)
- ✅ Main App (FastAPI)

### Step 6: Wait for Models to Download

```bash
# Check progress
docker-compose logs -f llm-service

# Bạn sẽ thấy:
# "Downloading model..."
# "Loading model..."
# "Model loaded successfully"
```

⏳ **Hãy kiên nhẫn!** Lần đầu mất 10-30 phút tùy tốc độ internet.

### Step 7: Setup LocalStack AWS Services

Khi models đã download xong:

```bash
# Run setup script
python scripts/setup_localstack.py
```

**Script sẽ tạo**:
- ✅ S3 buckets: `chatbot-raw-data`, `chatbot-processed-data`, `chatbot-backups`
- ✅ DynamoDB table: `chatbot-conversations`
- ✅ Secrets: GitLab, Slack, Backlog credentials

### Step 8: Verify All Services

```bash
# Check all services are healthy
curl http://localhost:8000/health

# Expected output:
{
  "status": "healthy",
  "services": {
    "vector_store": "healthy",
    "conversation_store": "healthy",
    "orchestrator": "healthy",
    "embedding_service": "healthy",
    "llm_service": "healthy"
  }
}
```

### Step 9: Ingest Data (Optional)

```bash
# Fetch data from GitLab/Slack/Backlog
python scripts/run_data_fetcher.py

# Build vector index
python scripts/build_vector_index.py
```

### Step 10: Test Chatbot!

```bash
# Send a test message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hello! What can you help me with?\", \"conversation_id\": \"test-1\"}"

# Expected response:
{
  "conversation_id": "test-1",
  "answer": "I'm a chatbot that can help you with...",
  "sources": [],
  "processing_time": 3.5
}
```

✅ **SUCCESS!** Chatbot đã hoạt động!

---

## 🎯 Service Ports

| Service | Port | URL |
|---------|------|-----|
| **LocalStack Desktop** | 4566 | http://localhost:4566 |
| **Main App** | 8000 | http://localhost:8000 |
| **ChromaDB** | 8001 | http://localhost:8001 |
| **Embedding Service** | 8002 | http://localhost:8002 |
| **LLM Service** | 8003 | http://localhost:8003 |
| **PostgreSQL** | 5432 | localhost:5432 |
| **Redis** | 6379 | localhost:6379 |

---

## 🔍 Verify LocalStack Desktop

### Via Desktop UI

1. Open LocalStack Desktop
2. Click "Resources" tab
3. You should see:
   - S3 buckets (3)
   - DynamoDB tables (1)
   - Secrets (3)

### Via CLI

```bash
# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List DynamoDB tables
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# List Secrets
aws --endpoint-url=http://localhost:4566 secretsmanager list-secrets
```

---

## 🛠️ Common Issues

### ❌ Port 4566 Already in Use

**Solution**:
```bash
# Check what's using port 4566
netstat -ano | findstr :4566

# Stop conflicting service or restart LocalStack Desktop
```

### ❌ Models Not Downloading

**Solution**:
```bash
# Check internet connection
ping huggingface.co

# Check Docker Desktop has enough disk space (50GB+)

# Restart service
docker-compose restart llm-service
```

### ❌ LocalStack Desktop Not Starting

**Solution**:
1. Restart LocalStack Desktop app
2. Check Docker Desktop is running
3. Check auth key in .env is correct

### ❌ Services Can't Connect to LocalStack

**Solution**:
```bash
# Verify LocalStack is accessible
curl http://localhost:4566/_localstack/health

# Check .env has correct endpoint
cat .env | grep LOCALSTACK_ENDPOINT
# Should show: LOCALSTACK_ENDPOINT=http://localhost:4566
```

---

## 📊 Expected Timeline

| Step | Time |
|------|------|
| Start LocalStack Desktop | 30 seconds |
| Update .env | 2 minutes |
| Start Docker services | 2 minutes |
| **Download models** | **10-30 minutes** ⏳ |
| Setup LocalStack | 1 minute |
| Ingest data | 2-5 minutes |
| Build vector index | 2-5 minutes |
| **TOTAL** | **~20-45 minutes** |

---

## ✅ Final Checklist

- [ ] LocalStack Desktop running (port 4566)
- [ ] .env file updated with API keys
- [ ] docker-compose.yml: localstack service commented out
- [ ] Docker services started (chromadb, embedding, llm, postgres, redis, app)
- [ ] Models downloaded successfully
- [ ] LocalStack setup completed (S3, DynamoDB, Secrets)
- [ ] Data ingested (optional)
- [ ] Vector index built (optional)
- [ ] Health check passing: `curl http://localhost:8000/health`
- [ ] Test chat working

---

## 🎉 You're Done!

**Your chatbot is now running!**

### Next Steps:

1. **Test more queries**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What are the open bugs in GitLab?\", \"conversation_id\": \"test-2\"}"
```

2. **View conversation history**:
```bash
curl http://localhost:8000/conversation/test-2
```

3. **Search knowledge base**:
```bash
curl "http://localhost:8000/search?query=bug&limit=5"
```

4. **Build a UI** (optional):
   - React/Vue frontend
   - Connect to http://localhost:8000/chat

---

## 📖 Additional Documentation

- **Full Setup Guide**: [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)
- **LocalStack Desktop Details**: [LOCALSTACK_DESKTOP_SETUP.md](LOCALSTACK_DESKTOP_SETUP.md)
- **Architecture**: [LOCAL_ARCHITECTURE.md](LOCAL_ARCHITECTURE.md)
- **Main README**: [README_LOCAL.md](README_LOCAL.md)

---

## 🆘 Need Help?

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f llm-service
```

### LocalStack Desktop

- Open Desktop app → Logs tab
- Check status indicators
- Verify resources are created

### Community

- LocalStack Docs: https://docs.localstack.cloud
- GitHub Issues: Create issue with logs

---

**Happy Chatting! 🤖**

**Remember**: LocalStack Desktop phải luôn chạy khi bạn sử dụng chatbot!
