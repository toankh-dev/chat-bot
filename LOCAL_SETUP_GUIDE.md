# 🚀 Hướng Dẫn Setup Local với HuggingFace + LangChain + LocalStack

## 📋 Yêu Cầu Hệ Thống

### Minimum (CPU Only)
- **RAM**: 16GB
- **Storage**: 50GB free space
- **CPU**: 8 cores (Intel i7/AMD Ryzen 7 hoặc tốt hơn)
- **Response time**: 10-30 giây

### Recommended (với GPU)
- **RAM**: 32GB
- **GPU**: NVIDIA GPU với 12GB+ VRAM (RTX 3080/4070 trở lên)
- **Storage**: 100GB SSD
- **CPU**: 8+ cores
- **Response time**: 3-10 giây

### Software Requirements
- Docker Desktop (version 24.0+)
- Docker Compose (version 2.20+)
- Python 3.11+
- Git

---

## 📥 Bước 1: Clone và Chuẩn Bị

```bash
# Clone repository
cd c:\Users\toankh\Documents\chat-bot

# Create .env file from example
cp .env.example .env

# Edit .env and fill in your API keys
notepad .env
```

### Cấu hình quan trọng trong .env:

```bash
# External API Keys (BẮT BUỘC)
GITLAB_TOKEN=your_gitlab_token_here
SLACK_BOT_TOKEN=xoxb-your-slack-token-here
BACKLOG_API_KEY=your_backlog_key_here

# Model Configuration
EMBEDDING_DEVICE=cpu  # Đổi thành 'cuda' nếu có GPU
LLM_DEVICE=cpu        # Đổi thành 'cuda' nếu có GPU
LLM_LOAD_IN_4BIT=true # false nếu có đủ 24GB+ VRAM
```

---

## 🐳 Bước 2: Start Services với Docker Compose

### Option A: Start tất cả services cùng lúc

```bash
# Start all services
docker-compose up -d

# Xem logs
docker-compose logs -f
```

### Option B: Start từng service một (Recommended cho lần đầu)

```bash
# 1. Start LocalStack first
docker-compose up -d localstack
docker-compose logs -f localstack

# 2. Start ChromaDB
docker-compose up -d chromadb
docker-compose logs -f chromadb

# 3. Start Embedding Service (sẽ download model ~500MB, mất 2-5 phút)
docker-compose up -d embedding-service
docker-compose logs -f embedding-service

# 4. Start LLM Service (sẽ download model ~14GB, mất 10-30 phút)
docker-compose up -d llm-service
docker-compose logs -f llm-service

# 5. Start PostgreSQL & Redis
docker-compose up -d postgres redis

# 6. Start Main Application
docker-compose up -d app
docker-compose logs -f app
```

---

## ⏳ Bước 3: Chờ Models Download

**QUAN TRỌNG**: Lần chạy đầu tiên sẽ mất thời gian để download models:

```
Embedding Service: ~500MB (2-5 phút)
LLM Service: ~14GB (10-30 phút tùy tốc độ internet)
```

### Check status:

```bash
# Check embedding service
curl http://localhost:8002/health

# Check LLM service
curl http://localhost:8003/health

# Check main app
curl http://localhost:8000/health
```

**Khi nào ready?** Khi tất cả endpoints trả về `status: healthy`

---

## 🧪 Bước 4: Test Services

### Test Embedding Service

```bash
curl -X POST http://localhost:8002/embed \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello world", "こんにちは", "Xin chào"],
    "normalize": true
  }'
```

Expected response:
```json
{
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], [0.5, 0.6, ...]],
  "dimension": 384,
  "model": "paraphrase-multilingual-MiniLM-L12-v2",
  "processing_time": 0.05
}
```

### Test LLM Service

```bash
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is a chatbot?",
    "max_new_tokens": 100,
    "temperature": 0.7
  }'
```

---

## 📚 Bước 5: Setup LocalStack & Knowledge Base

### Initialize LocalStack Services

```bash
# Run setup script
python scripts/setup_localstack.py
```

Script này sẽ:
- Tạo S3 buckets
- Tạo DynamoDB tables
- Tạo Secrets Manager secrets
- Setup EventBridge schedules

### Ingest Data vào Knowledge Base

```bash
# Run data fetcher manually
python scripts/run_data_fetcher.py

# Or trigger via LocalStack Lambda
aws --endpoint-url=http://localhost:4566 lambda invoke \
  --function-name data_fetcher \
  --payload '{}' \
  response.json
```

### Build Vector Index

```bash
# Build ChromaDB index from S3 data
python scripts/build_vector_index.py
```

---

## 🎮 Bước 6: Sử Dụng Chatbot

### Web UI (nếu có)

```bash
# Mở browser
http://localhost:8000
```

### API Endpoint

```bash
# Send a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the open bugs in GitLab?",
    "conversation_id": "test-123"
  }'
```

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Show me all high-priority bugs",
        "conversation_id": "session-1"
    }
)

print(response.json()["answer"])
```

---

## 🔧 Troubleshooting

### Problem 1: Models không download

```bash
# Check logs
docker-compose logs embedding-service
docker-compose logs llm-service

# Manual download (trong container)
docker exec -it chatbot-embedding bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
```

### Problem 2: Out of Memory

```bash
# Giảm resources trong docker-compose.yml
# Hoặc enable swap

# Tăng Docker Desktop memory limit:
# Settings → Resources → Memory → 16GB+
```

### Problem 3: GPU không được detect

```bash
# Install NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Enable GPU in docker-compose.yml
# Uncomment dòng: runtime: nvidia

# Test GPU trong container
docker exec -it chatbot-llm python -c "import torch; print(torch.cuda.is_available())"
```

### Problem 4: LocalStack connection refused

```bash
# Restart LocalStack
docker-compose restart localstack

# Check if port 4566 is free
netstat -an | grep 4566

# Re-run setup
python scripts/setup_localstack.py
```

---

## 📊 Performance Tuning

### CPU Optimization

```bash
# Trong .env
EMBEDDING_BATCH_SIZE=16  # Giảm từ 32
LLM_MAX_NEW_TOKENS=256   # Giảm từ 512
```

### GPU Optimization

```bash
# Trong .env
EMBEDDING_DEVICE=cuda
LLM_DEVICE=cuda
LLM_LOAD_IN_4BIT=true  # Sử dụng quantization
```

### Caching

```bash
# Enable Redis caching
ENABLE_CACHING=true
REDIS_TTL=3600
```

---

## 🧹 Cleanup & Maintenance

### Stop All Services

```bash
docker-compose down
```

### Stop and Remove Data

```bash
docker-compose down -v
```

### Remove Downloaded Models

```bash
rm -rf models-cache/*
```

### Clean Docker Images

```bash
docker system prune -a
```

---

## 📝 Development Workflow

### Hot Reload (Main App)

```bash
# App code được mount vào container
# Chỉnh sửa code trong app/ → auto reload

# Xem logs
docker-compose logs -f app
```

### Rebuild Services

```bash
# Sau khi thay đổi Dockerfile hoặc requirements.txt
docker-compose build embedding-service
docker-compose up -d embedding-service
```

### Run Tests

```bash
# Unit tests
docker-compose exec app pytest tests/

# Integration tests
docker-compose exec app pytest tests/integration/
```

---

## 🚀 Production Deployment (Optional)

Khi muốn deploy lên server thật:

1. **Thay thế LocalStack bằng AWS thật**
```bash
LOCALSTACK_ENDPOINT=  # Leave empty to use real AWS
AWS_ACCESS_KEY_ID=your_real_key
AWS_SECRET_ACCESS_KEY=your_real_secret
```

2. **Sử dụng managed databases**
```bash
POSTGRES_HOST=your-rds-endpoint.amazonaws.com
REDIS_HOST=your-elasticache-endpoint.amazonaws.com
```

3. **Enable authentication**
```bash
ENABLE_AUTHENTICATION=true
```

4. **Use reverse proxy (Nginx)**
```bash
# Thêm nginx service vào docker-compose.yml
```

---

## 📖 Next Steps

1. ✅ Read [LOCAL_ARCHITECTURE.md](LOCAL_ARCHITECTURE.md) để hiểu kiến trúc
2. ✅ Customize agents trong `app/agents/`
3. ✅ Add custom tools trong `app/tools/`
4. ✅ Integrate frontend UI
5. ✅ Setup monitoring with Grafana

---

## 🆘 Cần Giúp Đỡ?

- Check logs: `docker-compose logs -f [service-name]`
- GitHub Issues: Create an issue with logs
- Documentation: Read code comments trong `app/` và `services/`

---

**Happy Coding! 🎉**
