# Kiến Trúc Local với HuggingFace + LangChain + LocalStack

## 🏗️ Kiến Trúc Mới (Local Development)

```
User Interface (Web/API)
    ↓
FastAPI Gateway (Port 8000)
    ↓
┌─────────────────────────────────────────┐
│  ORCHESTRATOR (LangChain Agent)         │
│  - Model: StableLM-Instruct-7B          │
│  - Framework: LangChain                 │
│  - Phân tích intent & điều phối         │
└─────────────────────────────────────────┘
    ├──► Vector Store (ChromaDB/FAISS)
    │    - Embeddings: MiniLM-L12-v2
    │    - GitLab/Slack/Backlog data
    │
    ├──► Report Agent (LangChain Tool)
    │    - Backlog API operations
    │    - Slack API operations
    │
    ├──► Summarize Agent (LangChain Tool)
    │    - Slack message analysis
    │    - StableLM summarization
    │
    └──► Code Review Agent (LangChain Tool)
         - GitLab code analysis
         - StableLM code review

LocalStack (Port 4566)
    ├─ S3 (raw data storage)
    ├─ DynamoDB (conversations)
    ├─ Secrets Manager (API keys)
    └─ Lambda (background jobs)
```

---

## 🔄 So Sánh: AWS Bedrock vs Local Setup

| Component | AWS Bedrock | Local Setup |
|-----------|-------------|-------------|
| **Embedding** | Amazon Titan v2 (1024 dim) | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim) |
| **LLM** | Claude 3.5 Sonnet | stabilityai/japanese-stablelm-instruct-alpha-7b-v2 |
| **Orchestrator** | Bedrock Agents | LangChain Agents |
| **Vector Store** | OpenSearch Serverless | ChromaDB / FAISS |
| **Object Storage** | S3 | LocalStack S3 |
| **Database** | DynamoDB | LocalStack DynamoDB / SQLite |
| **API Gateway** | AWS API Gateway | FastAPI |
| **Secrets** | Secrets Manager | LocalStack Secrets Manager / .env |
| **Cost** | $350-1400/month | **$0** (hardware only) |

---

## 📦 Tech Stack

### Python Dependencies
```
langchain==0.1.0
langchain-community==0.0.10
sentence-transformers==2.3.1
transformers==4.36.0
torch==2.1.0
chromadb==0.4.22
faiss-cpu==1.7.4
fastapi==0.109.0
uvicorn==0.27.0
boto3==1.34.0
localstack-client==2.5
python-dotenv==1.0.0
requests==2.31.0
```

### Infrastructure
```
Docker & Docker Compose
LocalStack (AWS services local)
PostgreSQL (optional - for conversation history)
Redis (optional - for caching)
```

---

## 🚀 Components Chi Tiết

### 1. Embedding Service
**Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Multilingual support (English, Japanese, Vietnamese)
- 384 dimensions (lighter than Titan's 1024)
- Fast inference (~50ms/doc)
- Runs on CPU or GPU

```python
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = embedder.encode(["Hello world", "こんにちは"])
```

### 2. LLM Orchestrator
**Model**: `stabilityai/japanese-stablelm-instruct-alpha-7b-v2`
- Japanese-optimized (good for Asian languages)
- 7B parameters (runnable on consumer GPU)
- Instruction-tuned for task following
- Memory: ~14GB RAM or 8GB VRAM (4-bit quantization)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "stabilityai/japanese-stablelm-instruct-alpha-7b-v2",
    load_in_4bit=True,  # Quantization for lower memory
    device_map="auto"
)
```

### 3. Vector Store
**Option A: ChromaDB** (Recommended for development)
- Persistent storage
- Built-in embedding support
- Easy querying
- Web UI for debugging

**Option B: FAISS**
- Faster search (for production)
- Lower memory
- No persistence (need to save/load)

### 4. LangChain Agents
Replace Bedrock Agents with LangChain's agent framework:

```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import HuggingFacePipeline

# Define tools
tools = [
    Tool(name="ReportAgent", func=report_agent_func),
    Tool(name="SummarizeAgent", func=summarize_agent_func),
    Tool(name="CodeReviewAgent", func=code_review_agent_func),
]

# Initialize agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)
```

---

## 🐳 Docker Setup

### Services
1. **LocalStack** - AWS services mock
2. **FastAPI App** - Main application
3. **Embedding Service** - Sentence Transformers API
4. **Vector Store** - ChromaDB
5. **PostgreSQL** (optional) - Conversation history
6. **Redis** (optional) - Caching

---

## 💾 Data Flow

### Ingestion Pipeline (EventBridge → Lambda)
```
1. Scheduled trigger (cron)
   ↓
2. Lambda: data_fetcher (LocalStack)
   - Fetch from GitLab/Slack/Backlog
   ↓
3. LocalStack S3
   - Store raw JSON documents
   ↓
4. Embedding Service
   - Generate embeddings with MiniLM
   ↓
5. ChromaDB / FAISS
   - Index vectors
```

### Query Pipeline (User → Response)
```
1. User sends question (FastAPI)
   ↓
2. Orchestrator Agent (LangChain + StableLM)
   - Analyze intent
   - Plan execution
   ↓
3. Tools Execution
   - Vector Store search (ChromaDB)
   - Agent invocation (Report/Summarize/Code Review)
   ↓
4. Response synthesis (StableLM)
   ↓
5. Save to LocalStack DynamoDB
   ↓
6. Return to user
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# LocalStack
LOCALSTACK_ENDPOINT=http://localhost:4566
AWS_DEFAULT_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# Models
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
LLM_MODEL=stabilityai/japanese-stablelm-instruct-alpha-7b-v2
USE_GPU=true
QUANTIZATION=4bit

# Vector Store
VECTOR_STORE=chromadb  # or faiss
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# API Keys (External Services)
GITLAB_TOKEN=your_gitlab_token
SLACK_BOT_TOKEN=your_slack_token
BACKLOG_API_KEY=your_backlog_key

# Application
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBUG=true
```

---

## 📊 Performance Comparison

### Latency Estimates

| Operation | AWS Bedrock | Local Setup |
|-----------|-------------|-------------|
| Embedding (1 doc) | ~100ms | ~50ms (GPU) / ~200ms (CPU) |
| LLM inference (100 tokens) | ~500ms | ~1-3s (GPU) / ~5-10s (CPU) |
| Vector search (1K docs) | ~100ms | ~50ms (FAISS) / ~100ms (ChromaDB) |
| End-to-end query | ~3s | ~5-15s (depending on hardware) |

### Hardware Requirements

**Minimum (CPU only)**:
- RAM: 16GB
- Storage: 50GB
- CPU: 8 cores
- Response time: 10-30s

**Recommended (GPU)**:
- RAM: 32GB
- GPU: 12GB VRAM (RTX 3080/4070 or better)
- Storage: 100GB SSD
- Response time: 3-10s

**Optimal (Production-like)**:
- RAM: 64GB
- GPU: 24GB VRAM (RTX 4090/A5000)
- Storage: 500GB NVMe SSD
- Response time: 2-5s

---

## 🎯 Advantages of Local Setup

### Pros ✅
1. **Zero cost** - No AWS charges
2. **Full control** - Customize everything
3. **Privacy** - Data stays local
4. **Fast iteration** - No deployment delays
5. **Offline capable** - Works without internet (after model download)
6. **Learning** - Deep understanding of internals

### Cons ❌
1. **Hardware requirements** - Need powerful machine
2. **Slower inference** - Compared to AWS optimized infrastructure
3. **No auto-scaling** - Fixed resources
4. **Maintenance** - Self-managed updates
5. **Initial setup** - More complex than managed service

---

## 🔐 Security

### Local Development
- LocalStack with default credentials
- `.env` file for secrets
- No external exposure (localhost only)

### Production Considerations (if deploying)
- Use proper AWS credentials
- Encrypt secrets with KMS
- Enable authentication (OAuth/JWT)
- Rate limiting
- Input validation

---

## 📝 Migration Steps

1. ✅ Install dependencies (Python, Docker, models)
2. ✅ Setup LocalStack with docker-compose
3. ✅ Create embedding service wrapper
4. ✅ Create LLM wrapper with LangChain
5. ✅ Implement ChromaDB vector store
6. ✅ Refactor agents as LangChain tools
7. ✅ Build FastAPI gateway
8. ✅ Update Lambda functions for LocalStack
9. ✅ Test end-to-end workflows
10. ✅ Document everything

---

## 🚀 Next Steps

1. Create `docker-compose.yml`
2. Build embedding service (`services/embedding/`)
3. Build LLM service (`services/llm/`)
4. Create FastAPI app (`app/`)
5. Update Lambda functions (`lambda/`)
6. Write setup scripts (`scripts/setup_local.sh`)
7. Test harness (`tests/`)

---

**Ready to start implementation? Let's build this! 🎉**
