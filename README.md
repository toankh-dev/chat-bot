# AWS Bedrock Multi-Agent Orchestrator Chatbot

Hệ thống chatbot thông minh sử dụng kiến trúc Multi-Agent Orchestrator với AWS Bedrock Agents để phối hợp nhiều agent chuyên biệt.

## 🏗️ Kiến Trúc

```
User Request
    ↓
API Gateway + Cognito
    ↓
Lambda: Chat Handler
    ↓
┌─────────────────────────────────────┐
│  ORCHESTRATOR AGENT (Bedrock Agent) │
│  - Phân tích câu hỏi                 │
│  - Lập kế hoạch execution            │
│  - Phối hợp các sub-agents          │
└─────────────────────────────────────┘
    ├──► Knowledge Base (GitLab/Slack/Backlog)
    ├──► Report Agent (Tạo tickets, post Slack)
    ├──► Summarize Agent (Phân tích Slack)
    └──► Code Review Agent (Review GitLab code)
```

## 📦 Cấu Trúc Project

```
kass/
├── docs/                              # Tài liệu chi tiết
│   ├── README.md                      # Tổng quan
│   ├── orchestrator-architecture.md   # Kiến trúc chi tiết
│   ├── orchestrator-implementation.md # Hướng dẫn implementation
│   ├── orchestrator-quickstart.md     # Hướng dẫn nhanh
│   └── orchestrator-terraform.md      # Terraform IaC
│
├── lambda/                            # Lambda functions
│   ├── data_fetcher/                  # Fetch data từ GitLab/Slack/Backlog
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   │
│   ├── orchestrator_actions/          # Action group cho Orchestrator
│   │   ├── lambda_function.py         # Invoke sub-agents
│   │   └── requirements.txt
│   │
│   ├── report_actions/                # Report Agent actions
│   │   ├── lambda_function.py         # Backlog/Slack integration
│   │   └── requirements.txt
│   │
│   ├── summarize_actions/             # Summarize Agent actions
│   │   ├── lambda_function.py         # Slack analysis
│   │   └── requirements.txt
│   │
│   ├── code_review_actions/           # Code Review Agent actions
│   │   ├── lambda_function.py         # GitLab code review
│   │   └── requirements.txt
│   │
│   └── chat_handler/                  # Entry point Lambda
│       ├── lambda_function.py         # Invoke Orchestrator Agent
│       └── requirements.txt
│
├── scripts/                           # Setup & deployment scripts
│   ├── setup_secrets.py
│   ├── setup_infrastructure.py
│   ├── create_agents.py
│   └── deploy_lambda.sh
│
└── tests/                             # Test suite
    ├── test_data_fetcher.py
    ├── test_multi_agent.py
    └── integration_test.py
```

## 🚀 Quick Start

### Bước 1: Chuẩn Bị

```bash
# Cài đặt AWS CLI
aws configure

# Verify
aws sts get-caller-identity
```

### Bước 2: Tạo Secrets

```bash
# GitLab
aws secretsmanager create-secret \
  --name /chatbot/gitlab/api-token \
  --secret-string '{"token":"YOUR_TOKEN","base_url":"https://gitlab.com/api/v4"}' \
  --region ap-southeast-1

# Slack
aws secretsmanager create-secret \
  --name /chatbot/slack/bot-token \
  --secret-string '{"bot_token":"xoxb-YOUR-TOKEN","signing_secret":"YOUR_SECRET"}' \
  --region ap-southeast-1

# Backlog
aws secretsmanager create-secret \
  --name /chatbot/backlog/api-key \
  --secret-string '{"api_key":"YOUR_KEY","space_url":"https://YOUR_SPACE.backlog.com"}' \
  --region ap-southeast-1
```

### Bước 3: Deploy Knowledge Base

```bash
# Chạy script setup infrastructure
cd scripts
python setup_infrastructure.py

# Deploy Knowledge Base (sử dụng Terraform hoặc script)
# Xem chi tiết trong docs/orchestrator-quickstart.md
```

### Bước 4: Tạo Bedrock Agents

```bash
# Orchestrator Agent
python create_agents.py --agent orchestrator

# Specialized Agents
python create_agents.py --agent report
python create_agents.py --agent summarize
python create_agents.py --agent code_review
```

### Bước 5: Deploy Lambda Functions

```bash
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

### Bước 6: Test

```bash
# Test simple query
python3 << 'EOF'
import boto3
bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

response = bedrock.invoke_agent(
    agentId='YOUR_ORCHESTRATOR_AGENT_ID',
    agentAliasId='YOUR_ALIAS_ID',
    sessionId='test-1',
    inputText='What are the open issues in GitLab?'
)

for event in response['completion']:
    if 'chunk' in event and 'bytes' in event['chunk']:
        print(event['chunk']['bytes'].decode('utf-8'), end='')
EOF
```

## 💡 Các Tính Năng Chính

### 1. Multi-Agent Orchestration

Orchestrator Agent tự động:
- Phân tích intent của user
- Quyết định sử dụng agent nào
- Thực thi tuần tự hoặc song song
- Tổng hợp kết quả

### 2. Specialized Agents

**Report Agent**
- Tạo Backlog tickets
- Post messages lên Slack
- Update tickets

**Summarize Agent**
- Lấy messages từ Slack
- Tóm tắt discussions
- Trích xuất action items

**Code Review Agent**
- Fetch GitLab MRs
- Analyze code changes
- Check coding standards

### 3. Knowledge Base

- Tìm kiếm semantic + keyword (hybrid)
- Vector embeddings với Amazon Titan
- OpenSearch Serverless
- Support GitLab, Slack, Backlog data

## 📖 Tài Liệu Chi Tiết

1. **[Architecture](docs/orchestrator-architecture.md)** - Kiến trúc hệ thống
2. **[Implementation Guide](docs/orchestrator-implementation.md)** - Hướng dẫn chi tiết
3. **[Quick Start](docs/orchestrator-quickstart.md)** - Deploy trong 2 giờ
4. **[Terraform IaC](docs/orchestrator-terraform.md)** - Infrastructure as Code

## 🎯 Ví Dụ Sử Dụng

### Simple Query

```
User: "Show me all high-priority bugs"
→ Orchestrator queries Knowledge Base
→ Returns list of bugs with citations
```

### Single Agent Action

```
User: "Create a Backlog ticket for the login bug"
→ Orchestrator invokes Report Agent
→ Report Agent creates ticket
→ Returns ticket URL
```

### Multi-Agent Workflow

```
User: "Summarize today's Slack discussions and create tickets for mentioned bugs"
→ Orchestrator plans:
  1. Summarize Agent → Get Slack messages & extract bugs
  2. Report Agent → Create tickets for each bug
→ Returns summary + ticket links
```

### Complex Coordination

```
User: "Generate weekly status report"
→ Orchestrator executes in parallel:
  ├─ Knowledge Base → Open issues count
  ├─ Summarize Agent → Slack activity
  └─ Code Review Agent → GitLab MR status
→ Synthesizes comprehensive report
```

## 💰 Chi Phí Ước Tính

### Development (10K requests/tháng)
- Bedrock Agents (4): ~$100-150
- Lambda: ~$10-20
- OpenSearch Serverless (1 OCU): ~$173
- Knowledge Base: ~$30-50
- DynamoDB: ~$10-20
- **Total: ~$350-500/tháng**

### Production (100K requests/tháng)
- Bedrock Agents (4): ~$200-400
- Lambda: ~$20-50
- OpenSearch Serverless (2-4 OCU): ~$350-700
- Knowledge Base: ~$50-100
- DynamoDB: ~$50-100
- ElastiCache: ~$25-50
- **Total: ~$700-1,400/tháng**

## 🔧 Development

### Lambda Functions Implementation Status

✅ **data_fetcher** - Hoàn thành (fetch GitLab/Slack/Backlog)
⏳ **orchestrator_actions** - Cần implement (invoke sub-agents)
⏳ **report_actions** - Cần implement (Backlog/Slack operations)
⏳ **summarize_actions** - Cần implement (Slack analysis)
⏳ **code_review_actions** - Cần implement (GitLab review)
⏳ **chat_handler** - Cần implement (API Gateway entry point)

### Next Steps

1. **Implement các Lambda actions** (xem docs/orchestrator-implementation.md)
2. **Create Bedrock Agents** (xem scripts/create_agents.py)
3. **Setup API Gateway** với Cognito
4. **Deploy và test** end-to-end

## 📚 Resources

- [AWS Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [OpenSearch Serverless](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)

## 🤝 Contributing

Xem [docs/orchestrator-implementation.md](docs/orchestrator-implementation.md) để hiểu chi tiết về cách implement các components.

## 📄 License

[Add your license]

---

**⚠️ Lưu Ý**: Đây là hệ thống Multi-Agent Orchestrator phức tạp. Nên đọc kỹ tài liệu trong thư mục `docs/` trước khi bắt đầu deploy.

**🚀 Bắt đầu**: Đọc [docs/orchestrator-quickstart.md](docs/orchestrator-quickstart.md) để deploy nhanh trong 2 giờ!
