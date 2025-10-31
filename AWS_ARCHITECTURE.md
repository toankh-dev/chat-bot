# AWS Architecture Design - KASS Chatbot

## 🎯 Migration Overview

Migrating from Docker-based local deployment to AWS serverless architecture for:
- **Scalability**: Auto-scaling based on demand
- **Cost Efficiency**: Pay-per-use with serverless
- **Reliability**: Multi-AZ deployment with AWS managed services
- **Security**: VPC isolation, IAM roles, encryption at rest/transit

---

## 🏗️ Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Client Applications                           │
│                    (Web, Mobile, Discord Bot, API)                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Amazon CloudFront (Optional)                     │
│                         - CDN for static assets                          │
│                         - DDoS protection                                │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Amazon API Gateway                               │
│  ┌──────────────────┬──────────────────┬──────────────────────────┐   │
│  │   REST API       │   WebSocket API  │   HTTP API (v2)          │   │
│  │   - /chat        │   - Real-time    │   - Lower cost           │   │
│  │   - /search      │   - Streaming    │   - Fast                 │   │
│  │   - /health      │                  │                          │   │
│  └──────────────────┴──────────────────┴──────────────────────────┘   │
│                                                                          │
│  Features:                                                               │
│  - Request throttling (10,000 RPS)                                     │
│  - API keys / Cognito auth                                              │
│  - Request/Response transformation                                      │
│  - CORS configuration                                                   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS Lambda Functions                             │
│                         (Python 3.11 runtime)                           │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Orchestrator Lambda (512MB-1GB)                               │   │
│  │  - Main chat handler                                            │   │
│  │  - Agent coordination (Bedrock Claude/Titan)                   │   │
│  │  - Tool invocation                                              │   │
│  │  - Timeout: 5 minutes                                           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Vector Search Lambda (512MB)                                  │   │
│  │  - Query OpenSearch vector index                               │   │
│  │  - Similarity search                                            │   │
│  │  - Metadata filtering                                           │   │
│  │  - Timeout: 30 seconds                                          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Document Processor Lambda (1GB-3GB)                           │   │
│  │  - S3 triggered                                                 │   │
│  │  - Excel/PDF chunking                                           │   │
│  │  - Bedrock embedding generation                                │   │
│  │  - Batch processing                                             │   │
│  │  - Timeout: 15 minutes                                          │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Tool Lambdas (256MB-512MB each)                               │   │
│  │  - Report Tool: Create tickets, notifications                  │   │
│  │  - Summarize Tool: Analyze conversations                       │   │
│  │  - Code Review Tool: GitLab integration                        │   │
│  │  - Timeout: 1-2 minutes                                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Discord Bot Handler Lambda (512MB)                            │   │
│  │  - EventBridge triggered                                        │   │
│  │  - Discord webhook integration                                  │   │
│  │  - Timeout: 30 seconds                                          │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Amazon Bedrock   │  │ Amazon OpenSearch│  │ Amazon DynamoDB  │
│                  │  │  Serverless      │  │                  │
│ - Claude 3.5     │  │                  │  │ Tables:          │
│   Sonnet         │  │ - Vector engine  │  │ - Conversations  │
│ - Claude 3 Haiku │  │ - k-NN search    │  │ - Messages       │
│ - Titan Text     │  │ - 1536/3072 dim  │  │ - Agent State    │
│ - Titan Embed    │  │ - Metadata filter│  │ - User Sessions  │
│ - Cohere Embed   │  │                  │  │ - Tool Logs      │
│                  │  │ Index:           │  │                  │
│ Features:        │  │ - knowledge_base │  │ Features:        │
│ - Guardrails     │  │ - 2 AZ replica   │  │ - On-demand      │
│ - Agents         │  │ - Auto-scaling   │  │ - TTL enabled    │
│ - Knowledge Base │  │ - VPC endpoint   │  │ - Streams        │
└──────────────────┘  └──────────────────┘  └──────────────────┘

        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Amazon S3        │  │ Amazon RDS       │  │ Amazon ElastiCache│
│                  │  │ (PostgreSQL)     │  │ (Redis)          │
│ Buckets:         │  │ Optional         │  │ Optional         │
│ - documents/     │  │                  │  │                  │
│ - embeddings/    │  │ db.t3.micro      │  │ - Query cache    │
│ - logs/          │  │ - Single AZ      │  │ - Session cache  │
│ - backups/       │  │ - 20GB storage   │  │ - Rate limiting  │
│                  │  │                  │  │                  │
│ Features:        │  │ Use case:        │  │ cache.t3.micro   │
│ - Versioning     │  │ - Complex queries│  │ (if needed)      │
│ - Lifecycle      │  │ - Transactions   │  │                  │
│ - Encryption     │  │ - Relational     │  │                  │
│ - S3 Select      │  │   analytics      │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘

        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon EventBridge                            │
│                                                                  │
│  Rules:                                                          │
│  - Document upload → Trigger processor Lambda                   │
│  - Scheduled embeddings → Daily batch job                       │
│  - Discord events → Bot handler Lambda                          │
│  - Failed operations → Dead letter queue                        │
└─────────────────────────────────────────────────────────────────┘

        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Logging                          │
│                                                                  │
│  - CloudWatch Logs (Lambda logs, API Gateway)                  │
│  - CloudWatch Metrics (Custom metrics, alarms)                 │
│  - X-Ray (Distributed tracing)                                 │
│  - CloudTrail (API audit logs)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Service Breakdown

### **1. Amazon Bedrock (LLM & Embeddings)**

**Primary LLM Models**:
- **Claude 3.5 Sonnet** - Main orchestrator (intelligent, context-aware)
- **Claude 3 Haiku** - Fast, cost-effective for simple queries
- **Titan Text Express/Lite** - Budget option for basic responses

**Embedding Models**:
- **Titan Embeddings V2** - 1024 dimensions, $0.0001/1K tokens
- **Cohere Embed English/Multilingual** - 1024 dimensions
- **Titan Multimodal Embeddings** - For images + text

**Features to Use**:
- **Bedrock Agents**: Built-in orchestration with action groups
- **Knowledge Bases**: Managed RAG with OpenSearch integration
- **Guardrails**: Content filtering, PII redaction
- **Model Invocation Logging**: CloudWatch integration

**Cost Estimate**:
- Input: $3/million tokens (Claude 3.5 Sonnet)
- Output: $15/million tokens
- Embeddings: $0.1/million tokens (Titan)

### **2. Amazon OpenSearch Serverless**

**Configuration**:
- **Type**: Vector engine with k-NN plugin
- **Indexing**: HNSW or IVF algorithm
- **Dimensions**: 1024 (Titan) or 3072 (custom)
- **Capacity**: Auto-scales 2-10 OCU (OpenSearch Compute Units)
- **Storage**: Auto-scales with data

**Index Schema**:
```json
{
  "mappings": {
    "properties": {
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 512,
            "m": 16
          }
        }
      },
      "text": { "type": "text" },
      "metadata": {
        "properties": {
          "source": { "type": "keyword" },
          "timestamp": { "type": "date" },
          "doc_id": { "type": "keyword" },
          "chunk_id": { "type": "keyword" }
        }
      }
    }
  }
}
```

**Cost Estimate**:
- OCU: $0.24/hour per unit (2 minimum = $350/month)
- Storage: $0.024/GB-month

### **3. AWS Lambda Functions**

**Function Architecture**:

| Function | Memory | Timeout | Concurrency | Trigger |
|----------|--------|---------|-------------|---------|
| Orchestrator | 1024MB | 300s | 100 | API Gateway |
| Vector Search | 512MB | 30s | 200 | Direct invoke |
| Doc Processor | 3008MB | 900s | 10 | S3/EventBridge |
| Report Tool | 512MB | 60s | 50 | Direct invoke |
| Summarize Tool | 512MB | 120s | 50 | Direct invoke |
| CodeReview Tool | 512MB | 120s | 50 | Direct invoke |
| Discord Handler | 512MB | 30s | 100 | EventBridge |

**Lambda Layers** (shared dependencies):
- `langchain-layer`: LangChain + dependencies (50MB)
- `aws-sdk-layer`: boto3 + AWS SDK (30MB)
- `data-processing-layer`: pandas, openpyxl (80MB)

**Cost Estimate** (1M requests/month):
- Requests: $0.20
- Compute: ~$8-12 (GB-seconds)
- **Total**: ~$10-15/month

### **4. Amazon DynamoDB**

**Table Design**:

**Conversations Table**:
```
PK: conversation_id (String)
SK: timestamp (Number)
Attributes:
  - user_id (String)
  - messages (List)
  - status (String)
  - ttl (Number) - Auto-delete after 30 days
  - created_at (String)
  - updated_at (String)

GSI: user_id-index
  PK: user_id
  SK: created_at
```

**Agent State Table**:
```
PK: agent_id (String)
SK: execution_id (String)
Attributes:
  - state (Map)
  - tool_calls (List)
  - intermediate_steps (List)
  - created_at (Number)
  - ttl (Number)
```

**Configuration**:
- **Billing**: On-demand (auto-scaling)
- **Encryption**: AWS managed keys
- **Backups**: Point-in-time recovery (35 days)
- **Streams**: Enabled for analytics

**Cost Estimate**:
- Write: $1.25/million requests
- Read: $0.25/million requests
- Storage: $0.25/GB-month
- **Typical**: $5-10/month

### **5. Amazon S3**

**Bucket Structure**:
```
kass-chatbot-{env}-{region}/
├── documents/
│   ├── excel/
│   ├── pdf/
│   └── raw/
├── embeddings/
│   └── processed/
├── logs/
│   ├── lambda/
│   └── api-gateway/
├── backups/
│   └── dynamodb/
└── cache/
    └── responses/
```

**Features**:
- **Versioning**: Enabled for documents
- **Lifecycle**: Move to Glacier after 90 days
- **Encryption**: SSE-S3 (AES-256)
- **Access**: VPC endpoints only
- **Events**: Trigger Lambda on upload

**Cost Estimate**:
- Storage: $0.023/GB-month (Standard)
- GET requests: $0.0004/1K
- PUT requests: $0.005/1K
- **Typical**: $5-10/month

### **6. Amazon RDS (Optional)**

**Configuration**:
- **Engine**: PostgreSQL 15
- **Instance**: db.t3.micro (2 vCPU, 1GB RAM)
- **Storage**: 20GB gp3
- **Multi-AZ**: No (single AZ for cost)
- **Backups**: 7-day retention

**Use Cases**:
- Complex analytics queries
- Relational data (users, permissions)
- Transaction-heavy operations
- Reporting dashboards

**Cost Estimate**: ~$15-20/month

**Recommendation**: Start with DynamoDB only, add RDS if needed

### **7. VPC & Networking**

**VPC Design**:
```
VPC: 10.0.0.0/16

Public Subnets (2 AZs):
  - 10.0.1.0/24 (us-east-1a) - NAT Gateway
  - 10.0.2.0/24 (us-east-1b) - NAT Gateway

Private Subnets (2 AZs):
  - 10.0.10.0/24 (us-east-1a) - Lambda, RDS
  - 10.0.11.0/24 (us-east-1b) - Lambda, RDS

VPC Endpoints:
  - S3 Gateway Endpoint (free)
  - DynamoDB Gateway Endpoint (free)
  - Bedrock Interface Endpoint ($7.2/month)
  - OpenSearch Interface Endpoint ($7.2/month)
```

**Security Groups**:
- **Lambda SG**: Outbound to Bedrock, OpenSearch, DynamoDB
- **RDS SG**: Inbound from Lambda SG only (port 5432)
- **OpenSearch SG**: Inbound from Lambda SG (port 443)

**Cost Estimate**:
- NAT Gateway: $32.4/month (if needed)
- Interface Endpoints: $14.4/month
- Data Transfer: $0.09/GB

**Optimization**: Use VPC endpoints to avoid NAT Gateway costs

---

## 💰 Total Cost Estimate

**Monthly Costs** (Medium usage: 100K requests, 10GB data):

| Service | Cost |
|---------|------|
| **Bedrock (LLM + Embeddings)** | $50-150 |
| **OpenSearch Serverless** | $350 |
| **Lambda** | $15 |
| **DynamoDB** | $10 |
| **S3** | $5 |
| **VPC Endpoints** | $15 |
| **API Gateway** | $3.5 |
| **CloudWatch Logs** | $5 |
| **Data Transfer** | $5 |
| **RDS (optional)** | $20 |
| **Total (without RDS)** | **$458-558/month** |
| **Total (with RDS)** | **$478-578/month** |

**Cost Optimization Strategies**:
1. Use **Claude Haiku** for simple queries (10x cheaper)
2. Cache frequent queries in DynamoDB (reduce LLM calls)
3. Use **S3 Select** for data filtering (cheaper than Lambda)
4. Implement request throttling
5. Use **Bedrock Knowledge Bases** (fully managed RAG)
6. Consider **OpenSearch t3.small** instead of Serverless ($60/month)

---

## 🔐 Security Architecture

### **1. IAM Roles & Policies**

**Lambda Execution Role**:
```yaml
Permissions:
  - logs:CreateLogGroup, PutLogEvents
  - dynamodb:GetItem, PutItem, Query
  - s3:GetObject, PutObject
  - bedrock:InvokeModel, InvokeModelWithResponseStream
  - aoss:APIAccessAll (OpenSearch)
  - secretsmanager:GetSecretValue
```

**API Gateway Role**:
```yaml
Permissions:
  - lambda:InvokeFunction
  - logs:CreateLogGroup, PutLogEvents
```

### **2. Encryption**

- **At Rest**:
  - S3: SSE-S3
  - DynamoDB: AWS managed keys
  - RDS: AES-256 encryption
  - OpenSearch: Encryption enabled

- **In Transit**:
  - TLS 1.2+ for all API calls
  - VPC endpoints for AWS services
  - Signed requests (SigV4)

### **3. Authentication & Authorization**

**Options**:
1. **API Keys**: Simple, low overhead
2. **AWS IAM**: For internal AWS services
3. **Amazon Cognito**: User pools for external users
4. **Lambda Authorizer**: Custom JWT validation

**Recommendation**: Start with API keys, add Cognito for production

---

## 📦 Deployment Strategy

### **Phase 1: Core Infrastructure** (Week 1)
- [x] VPC, subnets, security groups
- [x] S3 buckets
- [x] DynamoDB tables
- [x] IAM roles

### **Phase 2: AI Services** (Week 2)
- [x] Bedrock model access
- [x] OpenSearch Serverless collection
- [x] Test embedding pipeline

### **Phase 3: Lambda Functions** (Week 3)
- [x] Deploy Lambda functions
- [x] Create Lambda layers
- [x] Test invocations

### **Phase 4: API & Integration** (Week 4)
- [x] API Gateway setup
- [x] EventBridge rules
- [x] Integration testing

### **Phase 5: CI/CD** (Week 5)
- [x] CodePipeline setup
- [x] Automated deployments
- [x] Environment promotion

---

## 🚀 Next Steps

1. Choose IaC tool: **Terraform** (recommended) or **AWS CDK**
2. Set up AWS account and credentials
3. Create IaC templates
4. Refactor application code
5. Deploy infrastructure
6. Migrate data
7. Test and validate
8. Set up monitoring
9. Go live

---

**Key Decisions**:
- ✅ Use Bedrock (not self-hosted LLMs) - Managed, scalable
- ✅ Use OpenSearch Serverless - Auto-scaling, no ops
- ✅ Use DynamoDB (not RDS) initially - Lower cost, serverless
- ✅ Use Terraform for IaC - Industry standard, portable
- ✅ Multi-region: Start single region, plan for multi-region
