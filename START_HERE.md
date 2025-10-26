# 👋 START HERE - Multi-Agent Chatbot Setup

## 🚀 Quick Start (3 Bước)

### Bước 1: Choose Data Source

**🎮 RECOMMENDED: Discord (FREE & EASY!)** ⭐

Discord **miễn phí** và setup chỉ **5 phút**!

```bash
# Follow Discord setup guide (5 minutes)
# See: DISCORD_SETUP_GUIDE.md

# Then edit .env
cp .env.example .env
notepad .env

# Add Discord configuration:
USE_DISCORD=true
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_APPLICATION_ID=your_discord_app_id_here
DISCORD_GUILD_ID=your_discord_server_id_here
DISCORD_CHANNEL_IDS=channel_id_1,channel_id_2

# Keep these as false (unless you have tokens):
USE_GITLAB=false
USE_SLACK=false
USE_BACKLOG=false
```

**Alternative: GitLab/Slack/Backlog (Optional)**

Nếu bạn đã có tokens:

```bash
# Edit .env file
notepad .env

# Add API keys:
USE_GITLAB=true
USE_SLACK=true
USE_BACKLOG=true
GITLAB_TOKEN=your_gitlab_token_here
SLACK_BOT_TOKEN=xoxb_your_slack_token_here
BACKLOG_API_KEY=your_backlog_key_here
BACKLOG_SPACE_URL=https://your_space.backlog.com
```

### Bước 2: Start Services

```bash
# Start all services with Docker
docker-compose up -d

# Wait for models to download (first time: 10-30 minutes)
docker-compose logs -f llm-service
```

### Bước 3: Setup & Test

```bash
# Setup LocalStack resources
python scripts/setup_localstack.py

# Test chatbot
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hello\", \"conversation_id\": \"test-1\"}"
```

✅ **Done!** Chatbot đang chạy!

---

## 📖 Documentation Guide

**Bạn nên đọc theo thứ tự này**:

### 1. ⭐ DISCORD SETUP (Bắt đầu từ đây nếu dùng Discord!)
👉 **[DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md)**
- Step-by-step tạo Discord bot (5 phút)
- Get bot token, channel IDs
- FREE & EASY! ⭐
- **Đọc file này đầu tiên nếu bạn chọn Discord!**

### 2. 📚 DISCORD INTEGRATION (Code examples)
👉 **[DISCORD_INTEGRATION.md](DISCORD_INTEGRATION.md)**
- Discord data fetcher implementation
- Discord tools (report, summarize, code review)
- Usage examples & testing
- **Đọc sau khi setup Discord bot!**

### 3. 🐳 LOCALSTACK DOCKER SETUP
👉 **[LOCALSTACK_DOCKER.md](LOCALSTACK_DOCKER.md)**
- LocalStack với Docker setup
- Configuration details
- Troubleshooting

### 4. 📚 Full Guides
- **[LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)** - Complete setup guide
- **[LOCAL_ARCHITECTURE.md](LOCAL_ARCHITECTURE.md)** - Architecture details
- **[README.md](README.md)** - Main README

---

## ✅ What's Already Done

- ✅ `.env.example` template created
- ✅ `docker-compose.yml` configured for LocalStack Pro
- ✅ `.gitignore` created (protects .env)
- ✅ All application code implemented (3,500+ lines)
- ✅ All documentation written (2,000+ lines)
- ✅ Scripts ready (setup, data fetcher, vector indexing)

---

## ⏳ What You Need to Do

### 🎮 Option 1: Discord (RECOMMENDED!)

**Only 4 things** (takes ~10 minutes setup + 15-30 min model download):

1. **Create Discord bot** (5 minutes)
   - Follow [DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md)
   - Get bot token, app ID, channel IDs

2. **Add Discord config** to `.env`
   ```bash
   cp .env.example .env
   # Edit .env and add Discord credentials
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Run setup**
   ```bash
   python scripts/setup_localstack.py
   ```

**That's it!** 🎉

### 📊 Option 2: GitLab/Slack/Backlog (If you have tokens)

**Only 3 things**:

1. **Add API keys** to `.env`
   - GitLab token
   - Slack bot token
   - Backlog API key
   - Set `USE_GITLAB=true`, `USE_SLACK=true`, `USE_BACKLOG=true`

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Run setup**
   ```bash
   python scripts/setup_localstack.py
   ```

**That's it!** 🎉

---

## 🎯 Service Architecture

```
LocalStack (Port 4566) - Docker Container
    ↓
Main App (Port 8000)
    ├─ ChromaDB (8001) - Vector database
    ├─ Embedding Service (8002) - MiniLM (~500MB)
    ├─ LLM Service (8003) - StableLM (~14GB)
    ├─ PostgreSQL (5432) - Conversations
    └─ Redis (6379) - Cache
```

---

## 💾 Required Downloads

**First time only**:
- Embedding model: ~500MB (2-5 phút)
- LLM model: ~14GB (10-30 phút)

**Total**: ~15GB, mất 15-45 phút tùy internet

---

## 🔍 Health Check Commands

```bash
# LocalStack
curl http://localhost:4566/_localstack/health

# Main App
curl http://localhost:8000/health

# Embedding Service
curl http://localhost:8002/health

# LLM Service
curl http://localhost:8003/health
```

---

## 🆘 Common Issues

### ❌ Port 4566 in use
```bash
# Windows
netstat -ano | findstr :4566

# Linux/Mac
lsof -i :4566

# Stop conflicting service or restart LocalStack
docker-compose restart localstack
```

### ❌ Models not downloading
```bash
# Check logs
docker-compose logs -f llm-service

# Check internet, disk space (50GB+)
ping huggingface.co
```

### ❌ Services can't connect
```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs -f
```

---

## 📞 Need Help?

1. **Check logs**:
   ```bash
   docker-compose logs -f app
   docker-compose logs -f llm-service
   docker-compose logs -f localstack
   ```

2. **Read docs**:
   - Start: [README.md](README.md)
   - LocalStack: [LOCALSTACK_DOCKER.md](LOCALSTACK_DOCKER.md)
   - Full guide: [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)

3. **Verify setup**:
   ```bash
   # Check .env
   cat .env | grep LOCALSTACK

   # Test LocalStack
   curl http://localhost:4566/_localstack/health

   # Test all services
   docker-compose ps
   ```

---

## 🎉 Next Steps After Setup

### Test Basic Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What can you help me with?\", \"conversation_id\": \"demo\"}"
```

### Ingest Data (Optional)
```bash
# If using Discord:
python scripts/run_discord_fetcher.py

# If using GitLab/Slack/Backlog:
python scripts/run_data_fetcher.py

# Then build vector index
python scripts/build_vector_index.py
```

### Advanced Usage
```bash
# Search knowledge base
curl "http://localhost:8000/search?query=bug&limit=5"

# View conversations
curl http://localhost:8000/conversation/demo
```

---

## 📊 Project Statistics

**Total Implementation**:
- 32 files created
- 3,500+ lines of code
- 2,000+ lines of documentation
- 100% complete ✅

**Cost Comparison**:
- AWS Bedrock: $350-1,400/month
- GitLab/Slack/Backlog: $50-150/month
- Discord: **$0/month** (FREE!) 🎉
- This setup: **$0/month** (+ electricity ~$10-30)
- **Savings**: $400-1,550/month 💰

---

## 🎯 File Structure

```
chat-bot/
├── START_HERE.md                    ← YOU ARE HERE! ⭐
├── README.md                        ← Main README
├── DISCORD_SETUP_GUIDE.md           ← Read this first! (if using Discord)
├── DISCORD_INTEGRATION.md           ← Discord implementation details
├── LOCALSTACK_DOCKER.md             ← LocalStack Docker setup
├── LOCAL_SETUP_GUIDE.md             ← Complete setup guide
├── LOCAL_ARCHITECTURE.md            ← Architecture details
├── .env.example                     ← Environment template
├── docker-compose.yml               ← All services configuration
├── app/                             ← All code ready!
│   ├── main.py
│   ├── agents/
│   ├── tools/                       ← Discord support added! ✅
│   │   ├── report_tool.py          (Discord + Slack/Backlog)
│   │   ├── summarize_tool.py       (Discord + Slack)
│   │   └── code_review_tool.py     (Discord + GitLab)
│   ├── vector_store/
│   └── database/
├── lambda/
│   ├── discord_fetcher/             ← Discord data fetcher ✅
│   └── data_fetcher/                (GitLab/Slack/Backlog)
├── services/
│   ├── embedding/
│   └── llm/
├── scripts/
│   ├── setup_localstack.py
│   ├── run_discord_fetcher.py       ← Discord data ingestion
│   ├── run_data_fetcher.py
│   └── build_vector_index.py
└── docs/                            ← AWS Bedrock docs (legacy)
```

---

## ✅ Summary

**You have**:
✅ Complete chatbot system
✅ Docker configuration ready
✅ All code implemented
✅ All documentation ready
✅ **Discord integration added!** 🎮

**You need**:
⏳ Create Discord bot (5 minutes) OR add GitLab/Slack/Backlog keys
⏳ Start services with `docker-compose up -d`
⏳ Run setup script

**Time**:
- Setup: 10-15 phút
- Model download (first time): 15-40 phút
- **Total**: 25-55 phút

---

## 🚀 Let's Go!

### Using Discord (Recommended):
1. **Read**: [DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md) - Create bot (5 min)
2. **Read**: [DISCORD_INTEGRATION.md](DISCORD_INTEGRATION.md) - Implementation details
3. **Start**: `docker-compose up -d`

### Using GitLab/Slack/Backlog:
1. **Read**: [LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)
2. **Configure**: Add tokens to `.env`
3. **Start**: `docker-compose up -d`

---

**Happy Building! 🤖**

**Status**: Ready to start! ✅
**Docs**: Complete! ✅
**Discord Support**: Added! 🎮
