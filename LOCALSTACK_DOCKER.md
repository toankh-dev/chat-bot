# 🐳 LocalStack Docker Setup

## 📋 Tổng Quan

Hướng dẫn sử dụng **LocalStack Pro** với Docker để mô phỏng AWS services (S3, DynamoDB, Secrets Manager) trên máy local.

---

## ⚡ Quick Start

### 1. Cấu Hình .env

```bash
# Copy template
cp .env.example .env

# Edit .env và thêm LocalStack auth key
LOCALSTACK_AUTH_TOKEN=your_localstack_auth_token_here
LOCALSTACK_API_KEY=your_localstack_auth_token_here
LOCALSTACK_ENDPOINT=http://localhost:4566
```

### 2. Start LocalStack Container

```bash
# Start LocalStack service
docker-compose up -d localstack

# Check logs
docker-compose logs -f localstack
```

### 3. Verify LocalStack Running

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

### 4. Setup AWS Resources

```bash
# Create S3 buckets, DynamoDB tables, Secrets
python scripts/setup_localstack.py
```

### 5. Verify Resources Created

```bash
# List S3 buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List DynamoDB tables
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# List Secrets
aws --endpoint-url=http://localhost:4566 secretsmanager list-secrets
```

✅ **Done!** LocalStack đã sẵn sàng.

---

## 🔧 Docker Compose Configuration

File `docker-compose.yml` đã có sẵn LocalStack Pro configuration:

```yaml
localstack:
  image: localstack/localstack-pro:latest
  container_name: chatbot-localstack
  ports:
    - "4566:4566"
  environment:
    - LOCALSTACK_AUTH_TOKEN=${LOCALSTACK_AUTH_TOKEN}
    - LOCALSTACK_API_KEY=${LOCALSTACK_API_KEY}
    - SERVICES=s3,dynamodb,secretsmanager
    - DEBUG=1
    - PERSISTENCE=1
  volumes:
    - ./localstack-data:/var/lib/localstack
    - /var/run/docker.sock:/var/run/docker.sock
```

**Features**:
- ✅ **Persistence**: Data được lưu trong `./localstack-data`
- ✅ **Auto-start**: Khởi động cùng docker-compose
- ✅ **Pro features**: S3, DynamoDB, Secrets Manager

---

## 📊 Resources Created

### S3 Buckets

```bash
chatbot-raw-data           # Raw data from APIs
chatbot-processed-data     # Processed/cleaned data
chatbot-backups           # Backup files
```

### DynamoDB Tables

```bash
chatbot-conversations     # Chat history storage
```

### Secrets Manager

```bash
/chatbot/gitlab/api-token     # GitLab API token
/chatbot/slack/bot-token      # Slack bot token
/chatbot/backlog/api-key      # Backlog API key
```

---

## 🛠️ Common Commands

### Start/Stop Services

```bash
# Start LocalStack only
docker-compose up -d localstack

# Start all services
docker-compose up -d

# Stop LocalStack
docker-compose stop localstack

# Restart LocalStack
docker-compose restart localstack
```

### View Logs

```bash
# Follow logs
docker-compose logs -f localstack

# Last 100 lines
docker-compose logs --tail=100 localstack
```

### Clean Up

```bash
# Stop and remove container
docker-compose down localstack

# Remove data (CAUTION!)
rm -rf ./localstack-data

# Start fresh
docker-compose up -d localstack
python scripts/setup_localstack.py
```

---

## 🔍 Troubleshooting

### ❌ Problem: Auth Error

**Symptom**: Container fails to start with auth error

**Solution**:
```bash
# Check auth key in .env
cat .env | grep LOCALSTACK_AUTH

# Should show:
LOCALSTACK_AUTH_TOKEN=ls-siWACAyO-9014-qeMI-3043-qojItIhide54

# Restart container
docker-compose restart localstack
```

### ❌ Problem: Port 4566 Already in Use

**Symptom**: `Error: bind: address already in use`

**Solution**:
```bash
# Check what's using port 4566
# Windows:
netstat -ano | findstr :4566

# Linux/Mac:
lsof -i :4566

# Stop conflicting service or change port
```

### ❌ Problem: Services Can't Connect

**Symptom**: Application can't reach LocalStack

**Solution**:
```bash
# 1. Check LocalStack is running
docker-compose ps localstack

# 2. Check endpoint in .env
cat .env | grep LOCALSTACK_ENDPOINT
# Should be: http://localhost:4566

# 3. Test from host
curl http://localhost:4566/_localstack/health

# 4. Test from container
docker-compose exec app curl http://localstack:4566/_localstack/health
```

### ❌ Problem: Data Lost After Restart

**Symptom**: Resources disappear after restart

**Solution**:
```bash
# Check persistence is enabled
docker-compose config | grep PERSISTENCE
# Should show: PERSISTENCE=1

# Check volume exists
ls -la ./localstack-data

# If missing, recreate resources
python scripts/setup_localstack.py
```

---

## 💡 Tips & Best Practices

### 1. Secure Auth Key

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use .env.example as template only
```

### 2. Monitor Resources

```bash
# Check container stats
docker stats chatbot-localstack

# Check disk usage
du -sh ./localstack-data
```

### 3. Backup Important Data

```bash
# Backup LocalStack data
tar -czf localstack-backup.tar.gz ./localstack-data

# Restore backup
tar -xzf localstack-backup.tar.gz
```

---

## 🎯 Port Reference

| Service | Port | URL |
|---------|------|-----|
| LocalStack | 4566 | http://localhost:4566 |
| LocalStack Health | 4566 | http://localhost:4566/_localstack/health |

---

## 📖 Resources

- **LocalStack Docs**: https://docs.localstack.cloud
- **Pro Features**: https://docs.localstack.cloud/user-guide/aws/feature-coverage/
- **AWS CLI**: https://docs.aws.amazon.com/cli/

---

## ✅ Quick Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Add LocalStack auth key to `.env`
- [ ] Start LocalStack: `docker-compose up -d localstack`
- [ ] Verify running: `curl http://localhost:4566/_localstack/health`
- [ ] Setup resources: `python scripts/setup_localstack.py`
- [ ] Test S3: `aws --endpoint-url=http://localhost:4566 s3 ls`
- [ ] Test DynamoDB: `aws --endpoint-url=http://localhost:4566 dynamodb list-tables`

---

**LocalStack Docker ready! 🚀**
