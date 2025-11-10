# Quick Start Guide - GitLab Integration Testing

## 🚀 5-Minute Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your credentials
nano .env  # or use your favorite editor
```

**Required variables:**
```bash
GITLAB_API_TOKEN=your-gitlab-personal-access-token
GITLAB_WEBHOOK_SECRET=your-webhook-secret
KNOWLEDGE_BASE_GITLAB_ID=kb_gitlab
```

### 3. Start Services

```bash
# Start PostgreSQL and ChromaDB
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Run Tests

**Windows:**
```bash
run_tests.bat all
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh all
```

---

## 🧪 Test Commands Cheat Sheet

| Command | Description |
|---------|-------------|
| `run_tests.bat all` | Run all tests with coverage |
| `run_tests.bat unit` | Run only unit tests |
| `run_tests.bat integration` | Run only integration tests |
| `run_tests.bat gitlab` | Run only GitLab tests |
| `run_tests.bat fast` | Run tests without coverage (faster) |
| `run_tests.bat coverage` | Generate and open coverage report |
| `run_tests.bat failed` | Re-run only failed tests |

---

## 📝 Manual Testing Flow

### Step 1: Test GitLab Connection

```bash
# Start server
python src/main.py

# In another terminal, test connection
curl -X GET http://localhost:8000/api/v1/gitlab/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected:** Connection success with your GitLab username

---

### Step 2: Sync a Repository

```bash
curl -X POST http://localhost:8000/api/v1/gitlab/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-username/your-repo",
    "branch": "main",
    "knowledge_base_id": "kb_gitlab",
    "group_id": "test-group"
  }'
```

**Expected:** Repository synced successfully with `files_processed > 0`

---

### Step 3: Query Synced Code

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does the main function do?",
    "knowledge_base_id": "kb_gitlab"
  }'
```

**Expected:** Chatbot returns relevant code context

---

### Step 4: Test Webhook (Optional)

**Using ngrok:**

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Copy HTTPS URL and configure in GitLab:
# Repository → Settings → Webhooks
# URL: https://abc123.ngrok.io/api/v1/gitlab/webhook/push
# Secret: YOUR_GITLAB_WEBHOOK_SECRET
```

**Push a commit to trigger webhook:**

```bash
cd /path/to/your/repo
echo "# Test" >> README.md
git commit -am "test: trigger webhook"
git push
```

**Check server logs for:**
```
🔄 [Background] Starting webhook sync...
✅ [Background] Webhook sync completed: 1 files, 1 chunks
```

---

## 🎯 Success Criteria

### Automated Tests

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage ≥ 70%

Run: `run_tests.bat all`

### Manual Tests

- [ ] GitLab connection works
- [ ] Repository sync completes successfully
- [ ] Code is searchable in chatbot
- [ ] Webhook triggers auto-sync

Follow: [Manual Testing Guide](docs/GITLAB_TESTING_GUIDE.md)

---

## 🐛 Common Issues

### Issue 1: "GitLab authentication failed"

**Solution:**
1. Check `.env` has correct `GITLAB_API_TOKEN`
2. Generate new token: GitLab → Settings → Access Tokens
3. Token needs `api` scope

---

### Issue 2: "Docker containers not running"

**Solution:**
```bash
# Stop all containers
docker-compose down

# Restart
docker-compose up -d

# Check status
docker-compose ps
```

---

### Issue 3: "Tests failing due to missing dependencies"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

### Issue 4: "Coverage report not generated"

**Solution:**
```bash
# Generate manually
pytest tests/ --cov=src --cov-report=html

# Open report
start htmlcov\index.html  # Windows
open htmlcov/index.html   # Mac
```

---

## 📚 Next Steps

1. **Read Full Testing Guide:** [docs/GITLAB_TESTING_GUIDE.md](docs/GITLAB_TESTING_GUIDE.md)
2. **View Test Structure:** [tests/README.md](tests/README.md)
3. **Write Your Own Tests:** Follow templates in existing test files
4. **Run CI/CD Pipeline:** Push to trigger automated tests

---

## 🆘 Need Help?

- Check logs: `tail -f logs/app.log`
- View API docs: `http://localhost:8000/docs`
- Read troubleshooting: [docs/GITLAB_TESTING_GUIDE.md#troubleshooting](docs/GITLAB_TESTING_GUIDE.md#troubleshooting)

---

**Happy Testing!** 🎉
