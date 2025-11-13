# GitLab Integration - Testing Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Manual Testing](#manual-testing)
3. [Webhook Testing](#webhook-testing)
4. [Unit & Integration Tests](#unit--integration-tests)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### 1. Environment Setup

Create a `.env` file with GitLab configuration:

```bash
# Copy from .env.example
cp .env.example .env

# Configure GitLab credentials
GITLAB_URL=https://gitlab.com
GITLAB_API_TOKEN=your-personal-access-token
GITLAB_WEBHOOK_SECRET=your-secret-token-here
KNOWLEDGE_BASE_GITLAB_ID=kb_gitlab
```

### 2. Get GitLab Personal Access Token

1. Go to GitLab → Settings → Access Tokens
2. Create token with scopes:
   - `api` - Full API access
   - `read_repository` - Read repository content
   - `write_repository` - Write to repository
3. Copy token to `.env` file

### 3. Start Services

```bash
# Start PostgreSQL and ChromaDB
docker-compose up -d

# Start FastAPI server
python src/main.py
```

Server will run at: `http://localhost:8000`

---

## 🧪 Manual Testing

### Test 1: GitLab Connection

**Endpoint:** `GET /api/v1/gitlab/test`

```bash
# Get JWT token first
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'

# Test GitLab connection
curl -X GET http://localhost:8000/api/v1/gitlab/test \
  -H "Authorization: Bearer <your-jwt-token>"
```

**Expected Response:**
```json
{
  "username": "your-gitlab-username",
  "name": "Your Name",
  "email": "your@email.com",
  "gitlab_url": "https://gitlab.com",
  "connection": "success"
}
```

---

### Test 2: Manual Repository Sync

**Endpoint:** `POST /api/v1/gitlab/sync`

```bash
curl -X POST http://localhost:8000/api/v1/gitlab/sync \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://gitlab.com/your-username/your-repo",
    "branch": "main",
    "knowledge_base_id": "kb_gitlab",
    "group_id": "test-group",
    "domain": "general"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "repository": "your-repo",
  "branch": "main",
  "files_processed": 25,
  "files_failed": 0,
  "total_chunks": 25,
  "languages": {
    "python": 15,
    "javascript": 10
  },
  "total_lines": 1500,
  "total_bytes": 45000
}
```

**What to verify:**
- ✅ Repository cloned successfully
- ✅ Code files detected (check `languages`)
- ✅ Chunks created (`total_chunks` > 0)
- ✅ No failed files (`files_failed` = 0)

---

### Test 3: Query Synced Code

**Endpoint:** `POST /api/v1/ai/chat`

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does the main function do in this codebase?",
    "knowledge_base_id": "kb_gitlab",
    "chatbot_id": "chatbot-1",
    "conversation_id": "conv-1"
  }'
```

**Expected Response:**
```json
{
  "response": "Based on the code, the main function...",
  "sources": [
    {
      "file_path": "src/main.py",
      "line_start": 1,
      "line_end": 50,
      "score": 0.95
    }
  ]
}
```

**What to verify:**
- ✅ Chatbot returns relevant code context
- ✅ Sources include file paths from your repository
- ✅ Answers are accurate based on your code

---

## 🔔 Webhook Testing

### Step 1: Expose Local Server (for testing)

Use ngrok to expose localhost:

```bash
# Install ngrok
npm install -g ngrok

# Expose port 8000
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

---

### Step 2: Configure GitLab Webhook

1. Go to your GitLab repository → **Settings → Webhooks**
2. Configure webhook:
   - **URL:** `https://abc123.ngrok.io/api/v1/gitlab/webhook/push`
   - **Secret Token:** (same as `GITLAB_WEBHOOK_SECRET` in `.env`)
   - **Trigger:**
     - ✅ Push events
     - ✅ Merge request events
   - **SSL verification:** ✅ Enable

3. Click **Add webhook**

---

### Step 3: Test Webhook

**Option A: Test from GitLab UI**

1. GitLab → Settings → Webhooks → Your webhook → **Test**
2. Select "Push events"
3. Check server logs for webhook processing

**Option B: Test with Real Push**

```bash
# Make a change in your repository
cd /path/to/your/repo
echo "# Test webhook" >> README.md
git add README.md
git commit -m "test: trigger webhook"
git push origin main
```

**Expected Server Logs:**
```
INFO: POST /api/v1/gitlab/webhook/push - 202 Accepted
🔄 [Background] Starting webhook sync for https://gitlab.com/user/repo (commit: abc12345)
✅ [Background] Webhook sync completed: 1 files, 1 chunks
```

---

### Step 4: Verify Auto-Sync

Query the updated code immediately:

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What changed in the latest commit?",
    "knowledge_base_id": "kb_gitlab"
  }'
```

**Expected:** Chatbot should mention the new changes from your commit!

---

## 🧪 Unit & Integration Tests

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run only GitLab tests
pytest tests/test_gitlab*.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

### Test Structure

```
tests/
├── unit/
│   ├── test_gitlab_service.py          # GitLabService unit tests
│   ├── test_code_chunking_service.py   # CodeChunkingService unit tests
│   └── test_gitlab_sync_service.py     # GitLabSyncService unit tests
└── integration/
    ├── test_gitlab_endpoints.py        # API endpoint tests
    └── test_webhook_integration.py     # Webhook end-to-end tests
```

---

### Test Coverage Goals

| Component | Coverage Target | Status |
|-----------|----------------|--------|
| GitLabService | ≥ 80% | ⏳ |
| CodeChunkingService | ≥ 80% | ⏳ |
| GitLabSyncService | ≥ 70% | ⏳ |
| GitLabController | ≥ 70% | ⏳ |
| Webhook Handler | ≥ 80% | ⏳ |

---

## 🔍 Troubleshooting

### Issue 1: "Invalid GitLab token"

**Error:**
```
GitLab authentication failed: 401 Unauthorized
```

**Solution:**
1. Check `.env` file has correct `GITLAB_API_TOKEN`
2. Verify token has `api` scope
3. Token might be expired - generate new one

---

### Issue 2: "Webhook not triggered"

**Checklist:**
- ✅ Webhook URL is correct (use ngrok for local)
- ✅ Secret token matches `.env` file
- ✅ Push events are enabled in GitLab
- ✅ Server is running and accessible

**Debug:**
```bash
# Check webhook delivery in GitLab
GitLab → Settings → Webhooks → Recent Deliveries
```

---

### Issue 3: "Background sync failed"

**Error in logs:**
```
❌ [Background] Webhook sync failed: ...
```

**Common causes:**
1. **File not found** - File was deleted in commit
2. **Invalid encoding** - Binary files in changed files
3. **Embedding API error** - Gemini/Bedrock quota exceeded

**Solution:**
- Check server logs for specific error
- Verify file exists in repository
- Check embedding service quota

---

### Issue 4: "Code not searchable after sync"

**Checklist:**
- ✅ Sync completed successfully (`files_processed` > 0)
- ✅ Knowledge Base ID matches query (`kb_gitlab`)
- ✅ Embeddings were created (check ChromaDB)
- ✅ Wait a few seconds for indexing

**Verify embeddings:**
```bash
# Check ChromaDB collection
curl http://localhost:8000/chroma/api/v1/collections/kb_gitlab
```

---

## 📊 Test Scenarios

### Scenario 1: New Repository Sync
1. Add new repository to GitLab
2. Sync via API
3. Verify code searchable
4. Configure webhook
5. Push change
6. Verify auto-update

**Expected Time:** ~5 minutes

---

### Scenario 2: Large Repository
1. Sync repository with 100+ files
2. Verify batch processing works
3. Check memory usage
4. Query performance

**Expected Time:** ~10-15 minutes

---

### Scenario 3: Multiple Branches
1. Sync `main` branch
2. Sync `develop` branch
3. Verify both are searchable
4. Test webhook on both branches

**Expected Time:** ~10 minutes

---

### Scenario 4: Error Handling
1. Sync with invalid token
2. Sync non-existent repository
3. Webhook with wrong secret
4. Large file (>50KB) chunking

**Expected Time:** ~5 minutes

---

## ✅ Success Criteria

### Manual Testing
- [ ] GitLab connection successful
- [ ] Repository sync works (files_processed > 0)
- [ ] Code searchable in chatbot
- [ ] Webhook configured correctly
- [ ] Auto-sync on push works

### Automated Testing
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage ≥ 70%
- [ ] No memory leaks
- [ ] Performance benchmarks met

---

## 📝 Next Steps

1. **Run manual tests** following this guide
2. **Run automated tests** with pytest
3. **Report issues** if any test fails
4. **Deploy to production** after all tests pass

---

**Need Help?**
- Check logs: `tail -f logs/app.log`
- Review API docs: `http://localhost:8000/docs`
- Open issue on GitHub
