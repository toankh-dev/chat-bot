# 🖥️ LocalStack Desktop Setup Guide

## 📋 Tổng Quan

Bạn đang sử dụng **LocalStack Desktop** với auth key. Có 2 cách setup:

1. **Option A**: Sử dụng LocalStack Desktop app (Recommended)
2. **Option B**: Sử dụng Docker với LocalStack Pro image

---

## ✅ Option A: Sử dụng LocalStack Desktop App (Recommended)

### Bước 1: Cài Đặt LocalStack Desktop

1. Download LocalStack Desktop từ: https://localstack.cloud/download
2. Install và mở LocalStack Desktop
3. Login với auth key của bạn

### Bước 2: Start LocalStack Desktop

1. Mở LocalStack Desktop app
2. Click **Start LocalStack**
3. Verify đang chạy trên port **4566**

### Bước 3: Cấu Hình .env

```bash
# Copy .env.example
cp .env.example .env

# Edit .env
LOCALSTACK_ENDPOINT=http://localhost:4566
LOCALSTACK_AUTH_TOKEN=ls-siWACAyO-9014-qeMI-3043-qojItIhide54
LOCALSTACK_API_KEY=ls-siWACAyO-9014-qeMI-3043-qojItIhide54

# API Keys khác
GITLAB_TOKEN=your_token
SLACK_BOT_TOKEN=your_token
BACKLOG_API_KEY=your_key
```

### Bước 4: Comment LocalStack Service trong docker-compose.yml

```yaml
# Edit docker-compose.yml
# Comment toàn bộ localstack service vì đã dùng Desktop app

services:
  # LocalStack - COMMENTED OUT (using Desktop app)
  # localstack:
  #   image: localstack/localstack-pro:latest
  #   ...

  # ChromaDB - Keep this
  chromadb:
    image: chromadb/chroma:latest
    ...
```

### Bước 5: Start Services (Không bao gồm LocalStack)

```bash
# Start tất cả services NGOẠI TRỪ localstack
docker-compose up -d chromadb embedding-service llm-service postgres redis app
```

### Bước 6: Verify LocalStack Desktop

```bash
# Test connection
curl http://localhost:4566/_localstack/health

# Expected response:
{
  "services": {
    "s3": "running",
    "dynamodb": "running",
    "secretsmanager": "running",
    ...
  }
}
```

### Bước 7: Setup AWS Services

```bash
# Run setup script
python scripts/setup_localstack.py

# Script sẽ tạo:
# - S3 buckets
# - DynamoDB tables
# - Secrets Manager secrets
```

---

## 🐳 Option B: Sử dụng Docker với LocalStack Pro Image

### Bước 1: Cấu Hình .env

```bash
cp .env.example .env

# Edit .env - ADD auth key
LOCALSTACK_AUTH_TOKEN=ls-siWACAyO-9014-qeMI-3043-qojItIhide54
LOCALSTACK_API_KEY=ls-siWACAyO-9014-qeMI-3043-qojItIhide54
```

### Bước 2: docker-compose.yml đã được update

File đã có sẵn LocalStack Pro configuration:

```yaml
localstack:
  image: localstack/localstack-pro:latest
  environment:
    - LOCALSTACK_AUTH_TOKEN=${LOCALSTACK_AUTH_TOKEN}
    - LOCALSTACK_API_KEY=${LOCALSTACK_API_KEY}
```

### Bước 3: Start Tất Cả Services

```bash
# Start all services INCLUDING LocalStack
docker-compose up -d
```

### Bước 4: Verify

```bash
# Check LocalStack logs
docker-compose logs -f localstack

# Test connection
curl http://localhost:4566/_localstack/health
```

### Bước 5: Setup

```bash
python scripts/setup_localstack.py
```

---

## 🔍 Verify Setup

### Test S3

```bash
# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Expected output:
chatbot-raw-data
chatbot-processed-data
chatbot-backups
```

### Test DynamoDB

```bash
# List tables
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# Expected output:
{
  "TableNames": ["chatbot-conversations"]
}
```

### Test Secrets Manager

```bash
# List secrets
aws --endpoint-url=http://localhost:4566 secretsmanager list-secrets

# Expected output:
{
  "SecretList": [
    { "Name": "/chatbot/gitlab/api-token" },
    { "Name": "/chatbot/slack/bot-token" },
    { "Name": "/chatbot/backlog/api-key" }
  ]
}
```

---

## 🛠️ Troubleshooting

### Problem: Connection Refused

```bash
# Check if LocalStack is running
# Option A (Desktop):
# - Open LocalStack Desktop app
# - Verify status shows "Running"

# Option B (Docker):
docker-compose ps localstack
docker-compose logs localstack
```

### Problem: Auth Error

```bash
# Verify auth key in .env
cat .env | grep LOCALSTACK_AUTH

# Should show your auth key:
LOCALSTACK_AUTH_TOKEN=ls-siWACAyO-9014-qeMI-3043-qojItIhide54
```

### Problem: Port Already in Use

```bash
# Check what's using port 4566
# Windows:
netstat -ano | findstr :4566

# Linux/Mac:
lsof -i :4566

# Stop conflicting service or change port
```

---

## 📊 So Sánh: Desktop vs Docker

| Feature | Desktop App | Docker Container |
|---------|-------------|------------------|
| **Setup** | Click & start | Edit docker-compose |
| **Performance** | Native | Container overhead |
| **UI** | Desktop UI ✅ | CLI only |
| **Auto-start** | Can auto-start | Manual start |
| **Resource** | Lighter | Heavier |
| **Logs** | UI logs | docker logs |

**Recommendation**: Dùng **Desktop App** nếu có, dễ hơn và có UI!

---

## 🎯 Quick Start Checklist

### Nếu dùng Desktop App:

- [ ] Install LocalStack Desktop
- [ ] Start LocalStack Desktop app
- [ ] Verify running on port 4566
- [ ] Comment localstack service trong docker-compose.yml
- [ ] Copy .env.example → .env
- [ ] Add auth key vào .env
- [ ] Add API keys (GitLab, Slack, Backlog)
- [ ] Start other services: `docker-compose up -d chromadb embedding-service llm-service postgres redis app`
- [ ] Run: `python scripts/setup_localstack.py`
- [ ] Test: `curl http://localhost:4566/_localstack/health`

### Nếu dùng Docker:

- [ ] Copy .env.example → .env
- [ ] Add auth key vào .env
- [ ] Add API keys (GitLab, Slack, Backlog)
- [ ] Start all services: `docker-compose up -d`
- [ ] Run: `python scripts/setup_localstack.py`
- [ ] Test: `curl http://localhost:4566/_localstack/health`

---

## 💡 Best Practices

### 1. Keep Auth Key Secure

```bash
# NEVER commit .env to git
echo ".env" >> .gitignore

# Use .env.example as template only
```

### 2. Monitor LocalStack

```bash
# Desktop App: Check UI
# Docker: Check logs
docker-compose logs -f localstack
```

### 3. Backup Data

```bash
# LocalStack Desktop: Uses persistent data
# Docker: Volume is mounted at ./localstack-data
```

---

## 🔗 Resources

- **LocalStack Desktop**: https://localstack.cloud/download
- **LocalStack Docs**: https://docs.localstack.cloud
- **Pro Features**: https://docs.localstack.cloud/user-guide/aws/feature-coverage/

---

## 🆘 Need Help?

### LocalStack Desktop Issues

1. Check LocalStack Desktop logs (UI → Logs tab)
2. Restart LocalStack Desktop
3. Check port 4566 availability

### Docker Issues

```bash
# Check container
docker-compose ps localstack

# Check logs
docker-compose logs localstack

# Restart
docker-compose restart localstack
```

---

## ✅ Current Setup (Your Config)

**Auth Key**: `ls-siWACAyO-9014-qeMI-3043-qojItIhide54`
**Endpoint**: `http://localhost:4566`
**Region**: `ap-southeast-1`

**Status**: ✅ Configured in `.env.example` and `docker-compose.yml`

**Next Step**:
1. Copy `.env.example` → `.env`
2. Choose Option A (Desktop) or Option B (Docker)
3. Follow checklist above

---

**Happy LocalStack-ing! 🚀**
