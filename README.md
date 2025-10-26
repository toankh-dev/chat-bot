# 🤖 Multi-Agent Chatbot

> **Hệ thống chatbot thông minh chạy hoàn toàn trên Local với HuggingFace Models**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

---

## 🎯 Tổng Quan

Hệ thống Multi-Agent Chatbot sử dụng:
- 🤗 **HuggingFace Models** (StableLM-7B, MiniLM) - Miễn phí, chạy local
- 🦜 **LangChain** - Agent orchestration framework
- ☁️ **LocalStack** - AWS services mock (S3, DynamoDB, Secrets Manager)
- 🗄️ **ChromaDB** - Vector database
- 🎮 **Discord** - Data source (thay thế GitLab/Slack/Backlog)

### ⚡ Tính Năng Chính

- ✅ **Multi-Agent Architecture**: Orchestrator phối hợp các agent chuyên biệt
- ✅ **RAG (Retrieval-Augmented Generation)**: Truy xuất context từ vector database
- ✅ **Conversation Memory**: Lưu trữ lịch sử chat trong DynamoDB
- ✅ **Discord Integration**: Fetch và phân tích Discord messages
- ✅ **Code Review**: Phân tích code snippets
- ✅ **Report Generation**: Tạo báo cáo từ dữ liệu
- ✅ **100% Local**: Không cần AWS, data không rời khỏi máy

### 💰 Chi Phí

| AWS Bedrock (Cloud) | Local Setup (Bản này) |
|--------------------|-----------------------|
| $350-1,400/tháng | **$0** ✅ |

---

## 🚀 Quick Start

### Điều Kiện Tiên Quyết

- Docker Desktop (4GB+ RAM allocated)
- Python 3.11+
- 16GB+ RAM (recommend 32GB)
- 50GB+ disk space

### 3 Bước Setup

#### 1. Clone & Configure

```bash
# Clone repository
git clone <your-repo-url>
cd chat-bot

# Copy environment template
cp .env.example .env

# Edit .env - Add Discord credentials (optional)
USE_DISCORD=true
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_IDS=your_channel_ids
```

#### 2. Start Services

```bash
# Start all services (first time: download models ~15GB)
docker-compose up -d

# Wait for models to download (10-30 minutes)
docker-compose logs -f llm-service

# Setup LocalStack resources
python scripts/setup_localstack.py
```

#### 3. Test Chatbot

```bash
# Health check
curl http://localhost:8000/health

# Send test message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "conversation_id": "test-1"}'
```

✅ **Done!** Chatbot đang chạy tại `http://localhost:8000`

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[START_HERE.md](START_HERE.md)** | ⭐ Bắt đầu từ đây! Quick start guide |
| **[LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)** | Hướng dẫn setup chi tiết |
| **[LOCAL_ARCHITECTURE.md](LOCAL_ARCHITECTURE.md)** | Kiến trúc hệ thống |
| **[LOCALSTACK_DOCKER.md](LOCALSTACK_DOCKER.md)** | LocalStack Docker setup |
| **[DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md)** | Setup Discord bot (5 phút) |
| **[DISCORD_INTEGRATION.md](DISCORD_INTEGRATION.md)** | Discord integration code |

> **Note**: Thư mục `docs/` chứa tài liệu AWS Bedrock (legacy) - Phiên bản cloud cũ, tốn phí

---

## 🏗️ Architecture

```
User Request
    ↓
FastAPI App (Port 8000)
    ↓
┌─────────────────────────────────┐
│  ORCHESTRATOR AGENT (LangChain) │
│  - Phân tích câu hỏi            │
│  - Lập kế hoạch execution       │
│  - Phối hợp các tools           │
└─────────────────────────────────┘
    ├──► Vector Store (ChromaDB) - RAG retrieval
    ├──► LLM Service (StableLM-7B) - Text generation
    ├──► Embedding Service (MiniLM) - Text embeddings
    ├──► Discord Tool - Fetch messages
    ├──► Report Tool - Generate reports
    └──► Code Review Tool - Analyze code
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | StabilityAI/stablelm-zephyr-3b |
| **Embeddings** | sentence-transformers/all-MiniLM-L12-v2 |
| **Framework** | LangChain + FastAPI |
| **Vector DB** | ChromaDB |
| **Storage** | LocalStack S3 + DynamoDB |
| **Database** | PostgreSQL + Redis |
| **Orchestration** | Docker Compose |

---

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Main App | 8000 | http://localhost:8000 |
| ChromaDB | 8001 | http://localhost:8001 |
| Embedding Service | 8002 | http://localhost:8002 |
| LLM Service | 8003 | http://localhost:8003 |
| LocalStack | 4566 | http://localhost:4566 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## 🎮 Discord Integration (Recommended!)

Thay vì GitLab/Slack/Backlog (phức tạp, tốn phí), dùng **Discord** (miễn phí, 5 phút setup):

### Tại sao Discord?

- ✅ **Miễn phí** - Không cần paid plan
- ✅ **Dễ setup** - Chỉ 5 phút
- ✅ **Rich API** - Messages, threads, reactions, embeds
- ✅ **Webhook support** - Realtime notifications

### Quick Setup

```bash
# 1. Tạo Discord bot (5 phút)
# Xem: DISCORD_SETUP_GUIDE.md

# 2. Add credentials to .env
DISCORD_BOT_TOKEN=MTIzNDU2...
DISCORD_CHANNEL_IDS=111111,222222

# 3. Fetch data
python scripts/run_data_fetcher.py --source discord

# 4. Build index
python scripts/build_vector_index.py
```

Xem chi tiết: [DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md)

---

## 🛠️ Usage Examples

### Chat API

```bash
# Simple chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the recent Discord messages?",
    "conversation_id": "conv-123"
  }'

# Response:
{
  "conversation_id": "conv-123",
  "answer": "Based on recent messages...",
  "sources": ["discord_msg_1", "discord_msg_2"],
  "processing_time": 4.2
}
```

### Search Knowledge Base

```bash
# Search for context
curl "http://localhost:8000/search?query=bug&limit=5"

# Response:
{
  "results": [
    {
      "content": "Bug report from Discord...",
      "metadata": {"source": "discord", "channel": "dev"},
      "score": 0.89
    }
  ]
}
```

### View Conversation History

```bash
# Get conversation
curl http://localhost:8000/conversation/conv-123

# Response:
{
  "conversation_id": "conv-123",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

---

## 🔧 Development

### Project Structure

```
chat-bot/
├── app/                      # Main application
│   ├── main.py              # FastAPI app
│   ├── agents/              # LangChain agents
│   ├── tools/               # Agent tools
│   ├── llm/                 # LLM wrappers
│   └── stores/              # Data stores
├── services/                # Microservices
│   ├── embedding/           # Embedding service
│   └── llm/                 # LLM service
├── scripts/                 # Utility scripts
│   ├── setup_localstack.py
│   ├── run_data_fetcher.py
│   └── build_vector_index.py
├── lambda/                  # AWS Lambda functions (for cloud deployment)
├── docs/                    # AWS Bedrock documentation (legacy)
├── docker-compose.yml
├── .env.example
└── README.md
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run app locally (without Docker)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/
```

### Adding New Tools

```python
# app/tools/my_tool.py
from langchain.tools import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Tool description for LLM"

    def _run(self, query: str) -> str:
        # Tool logic
        return "Result"
```

---

## 🐛 Troubleshooting

### Models Not Downloading

```bash
# Check internet connection
ping huggingface.co

# Check Docker logs
docker-compose logs llm-service

# Restart service
docker-compose restart llm-service
```

### LocalStack Connection Error

```bash
# Verify LocalStack running
curl http://localhost:4566/_localstack/health

# Check .env configuration
cat .env | grep LOCALSTACK

# Restart LocalStack
docker-compose restart localstack
```

### ChromaDB Error

```bash
# Check ChromaDB status
curl http://localhost:8001/api/v1/heartbeat

# Clear and rebuild
docker-compose down chromadb
docker volume rm chat-bot_chroma-data
docker-compose up -d chromadb
python scripts/build_vector_index.py
```

---

## 📈 Performance

### Resource Usage

| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| LLM (StableLM-7B) | ~8GB | 2-4 cores | ~14GB |
| Embedding (MiniLM) | ~1GB | 1 core | ~500MB |
| ChromaDB | ~500MB | 1 core | Varies |
| PostgreSQL | ~200MB | 1 core | ~100MB |
| Redis | ~100MB | 1 core | ~50MB |
| **Total** | **~10GB** | **5-7 cores** | **~15GB** |

### Response Times

| Query Type | CPU | GPU (if available) |
|-----------|-----|---------------------|
| Simple QA | 5-10s | 2-3s |
| RAG Query | 8-15s | 3-5s |
| Code Review | 10-20s | 4-7s |

---

## 🔐 Security

- ✅ All credentials in `.env` (gitignored)
- ✅ No data sent to external APIs
- ✅ LocalStack for AWS mock (no cloud)
- ✅ Network isolated via Docker

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 🆘 Support

- **Documentation**: See docs above
- **Issues**: Create GitHub issue với logs
- **Discord Setup**: See [DISCORD_SETUP_GUIDE.md](DISCORD_SETUP_GUIDE.md)
- **LocalStack**: See [LOCALSTACK_DOCKER.md](LOCALSTACK_DOCKER.md)

---

## 🎉 Status

**Current Version**: v1.0.0 (Local Setup Complete)

- ✅ Core infrastructure implemented
- ✅ Multi-agent orchestration working
- ✅ Discord integration ready
- ✅ LocalStack configured
- ✅ Vector search functional
- ⏳ UI in development (optional)

---

**Built with ❤️ using Open Source**
