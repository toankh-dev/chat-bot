# AWS Migration Guide - KASS Chatbot

## 📋 Overview

This guide walks you through migrating the KASS Chatbot from Docker-based local deployment to AWS serverless architecture.

---

## 🎯 Migration Goals

✅ **Scalability**: Auto-scaling based on demand
✅ **Cost Efficiency**: Pay-per-use with serverless (est. $450-550/month)
✅ **Reliability**: Multi-AZ deployment with managed services
✅ **Security**: VPC isolation, IAM roles, encryption
✅ **Performance**: Low latency with regional deployment

---

## 📊 Architecture Changes

### **Before (Local)**
```
Docker Compose
├── FastAPI App (Port 8000)
├── ChromaDB (Vector DB)
├── PostgreSQL (Conversations)
├── Redis (Cache)
└── Gemini API (External)
```

### **After (AWS)**
```
AWS Cloud
├── API Gateway → REST API
├── Lambda Functions → Serverless compute
├── Bedrock → LLM & Embeddings
├── OpenSearch Serverless → Vector search
├── DynamoDB → Conversations & state
└── S3 → Document storage
```

---

## 🚀 Migration Steps

### **Phase 1: Prerequisites** (Day 1)

#### 1.1 AWS Account Setup
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json

# Verify
aws sts get-caller-identity
```

#### 1.2 Request Bedrock Model Access
```bash
# Go to AWS Console → Bedrock → Model access
# Request access to:
# - Claude 3.5 Sonnet
# - Claude 3 Haiku
# - Titan Text Express
# - Titan Embeddings V2

# Approval takes 5-10 minutes
```

#### 1.3 Install Terraform
```bash
# Windows (using Chocolatey)
choco install terraform

# Or download from: https://www.terraform.io/downloads

# Verify
terraform version
```

#### 1.4 Install Python Dependencies
```bash
cd lambda_functions

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### **Phase 2: Infrastructure Deployment** (Day 2-3)

#### 2.1 Configure Terraform Backend
```bash
cd terraform

# Create S3 bucket for Terraform state (one-time setup)
aws s3 mb s3://kass-chatbot-terraform-state --region us-east-1

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name kass-chatbot-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

#### 2.2 Initialize Terraform
```bash
# Initialize with backend config
terraform init \
  -backend-config="bucket=kass-chatbot-terraform-state" \
  -backend-config="key=dev/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=kass-chatbot-terraform-locks"
```

#### 2.3 Plan Deployment
```bash
# Review what will be created
terraform plan -var-file=environments/dev/terraform.tfvars

# Expected resources: ~50-60
# - VPC and subnets
# - Security groups
# - IAM roles and policies
# - S3 buckets
# - DynamoDB tables
# - OpenSearch collection
# - Lambda functions
# - API Gateway
# - EventBridge rules
```

#### 2.4 Deploy Infrastructure
```bash
# Deploy (takes 15-20 minutes)
terraform apply -var-file=environments/dev/terraform.tfvars

# Confirm with 'yes'

# Save outputs
terraform output -json > outputs.json
```

#### 2.5 Verify Deployment
```bash
# Check API Gateway
export API_URL=$(terraform output -raw api_gateway_url)
curl $API_URL/health

# Check OpenSearch
aws opensearchserverless get-collection \
  --id $(terraform output -raw opensearch_collection_id)

# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `kass-chatbot-dev`)]'
```

---

### **Phase 3: Data Migration** (Day 3-4)

#### 3.1 Export Existing Data

**From ChromaDB**:
```bash
# Run export script
python scripts/export_chromadb.py --output exports/chromadb_vectors.json

# Expected output: JSON with texts + metadata (embeddings will be regenerated)
```

**From PostgreSQL**:
```bash
# Export conversations
docker exec chatbot-postgres pg_dump -U chatbot -d chatbot -t conversations > exports/conversations.sql

# Or use Python script
python scripts/export_postgres.py --output exports/conversations.json
```

#### 3.2 Migrate to S3
```bash
# Upload documents
aws s3 sync ./embedding-data s3://kass-chatbot-dev-documents/excel/

# Upload exports
aws s3 cp exports/conversations.json s3://kass-chatbot-dev-backups/
```

#### 3.3 Generate Embeddings with Bedrock
```bash
# Run migration script
python scripts/migrate_to_bedrock.py \
  --input exports/chromadb_vectors.json \
  --collection-endpoint $(terraform output -raw opensearch_endpoint) \
  --index-name knowledge_base

# This will:
# 1. Read existing texts
# 2. Generate embeddings using Bedrock Titan
# 3. Index in OpenSearch
# 4. Takes ~10-30 minutes depending on data size
```

#### 3.4 Migrate Conversations to DynamoDB
```bash
# Run conversation migration
python scripts/migrate_conversations.py \
  --input exports/conversations.json \
  --table-name $(terraform output -raw conversations_table_name)

# Verify
aws dynamodb scan \
  --table-name $(terraform output -raw conversations_table_name) \
  --max-items 10
```

---

### **Phase 4: Lambda Deployment** (Day 4-5)

#### 4.1 Build Lambda Layers
```bash
cd lambda_functions

# Build dependencies layer
./scripts/build_layers.sh

# This creates:
# - layers/langchain-layer.zip (~50MB)
# - layers/aws-sdk-layer.zip (~30MB)
# - layers/data-processing-layer.zip (~80MB)
```

#### 4.2 Package Lambda Functions
```bash
# Package all functions
./scripts/package_lambdas.sh

# Creates deployment packages:
# - dist/orchestrator.zip
# - dist/vector_search.zip
# - dist/document_processor.zip
# - dist/report_tool.zip
# - dist/summarize_tool.zip
# - dist/code_review_tool.zip
# - dist/discord_handler.zip
```

#### 4.3 Deploy Lambda Functions
```bash
# Upload layers
aws lambda publish-layer-version \
  --layer-name kass-chatbot-dev-langchain \
  --zip-file fileb://layers/langchain-layer.zip \
  --compatible-runtimes python3.11

# Deploy functions (automated via Terraform)
terraform apply -var-file=environments/dev/terraform.tfvars -target=module.lambda

# Or use deployment script
python scripts/deploy_lambdas.py --environment dev
```

#### 4.4 Configure Environment Variables
```bash
# Set secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name kass-chatbot/dev/discord-token \
  --secret-string '{"token":"YOUR_DISCORD_TOKEN"}'

aws secretsmanager create-secret \
  --name kass-chatbot/dev/api-keys \
  --secret-string '{"slack":"xxx","gitlab":"xxx"}'
```

---

### **Phase 5: Testing** (Day 5-6)

#### 5.1 Unit Tests
```bash
# Run Lambda unit tests
cd lambda_functions
pytest tests/ -v

# Expected: All tests pass
```

#### 5.2 Integration Tests
```bash
# Test API endpoints
export API_URL=$(terraform output -raw api_gateway_url)
export API_KEY=$(aws apigateway get-api-keys --query 'items[0].value' --output text)

# Health check
curl -H "x-api-key: $API_KEY" $API_URL/health

# Chat test
curl -X POST $API_URL/chat \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! What can you help me with?",
    "conversation_id": "test-001"
  }'

# Vector search test
curl -X POST $API_URL/search \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project management",
    "limit": 5
  }'
```

#### 5.3 Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery run tests/load-test.yml

# Expected: 95% success rate, <3s latency
```

#### 5.4 End-to-End Testing
```bash
# Run E2E test suite
python scripts/run_e2e_tests.py --environment dev

# Tests:
# ✓ Document upload and processing
# ✓ Embedding generation
# ✓ Vector search
# ✓ Chat with RAG
# ✓ Conversation history
# ✓ Tool invocation
```

---

### **Phase 6: Monitoring Setup** (Day 6)

#### 6.1 CloudWatch Dashboards
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name kass-chatbot-dev \
  --dashboard-body file://monitoring/dashboard.json

# Dashboard includes:
# - API Gateway requests/errors/latency
# - Lambda invocations/errors/duration
# - DynamoDB read/write capacity
# - OpenSearch search latency
# - Bedrock API calls/throttles
```

#### 6.2 CloudWatch Alarms
```bash
# Create alarms
terraform apply -var-file=environments/dev/terraform.tfvars -target=module.monitoring

# Alarms:
# - High error rate (>5%)
# - High latency (>5s p99)
# - Lambda throttling
# - DynamoDB throttling
# - Cost anomaly
```

#### 6.3 X-Ray Tracing
```bash
# Enable X-Ray (already configured in Terraform)
# View traces:
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)

# Open AWS Console → X-Ray → Service Map
```

---

### **Phase 7: CI/CD Setup** (Day 7)

#### 7.1 GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r lambda_functions/requirements.txt
      - run: pytest tests/

  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: cd terraform && terraform init
      - run: cd terraform && terraform apply -var-file=environments/dev/terraform.tfvars -auto-approve

  deploy-prod:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      # Similar to deploy-dev but with manual approval
```

#### 7.2 Configure Secrets
```bash
# Add to GitHub repository secrets:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - DISCORD_TOKEN
# - SLACK_TOKEN
```

---

### **Phase 8: Production Deployment** (Day 8+)

#### 8.1 Create Production Environment
```bash
# Copy dev config
cp terraform/environments/dev/terraform.tfvars terraform/environments/prod/terraform.tfvars

# Edit prod values:
# - environment = "prod"
# - bedrock_llm_model_id = "anthropic.claude-3-5-sonnet..." (not Haiku)
# - opensearch_max_ocu = 6 (higher capacity)
# - enable_dynamodb_pitr = true
# - enable_waf = true
# - log_retention_days = 30
```

#### 8.2 Deploy to Production
```bash
# Initialize
terraform init \
  -backend-config="bucket=kass-chatbot-terraform-state" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=us-east-1"

# Plan
terraform plan -var-file=environments/prod/terraform.tfvars

# Apply (with approval)
terraform apply -var-file=environments/prod/terraform.tfvars
```

#### 8.3 Production Checklist
- [ ] Enable AWS WAF on API Gateway
- [ ] Configure custom domain with Route 53
- [ ] Set up SSL certificate with ACM
- [ ] Enable CloudTrail for audit logging
- [ ] Configure AWS Backup for DynamoDB
- [ ] Set up SNS for alarm notifications
- [ ] Enable GuardDuty for threat detection
- [ ] Configure AWS Cost Anomaly Detection
- [ ] Document incident response procedures
- [ ] Train team on monitoring and troubleshooting

---

## 💰 Cost Optimization

### **Immediate Savings**
1. **Use Claude Haiku for simple queries** (10x cheaper than Sonnet)
2. **Enable DynamoDB caching** (reduce LLM calls by 30-40%)
3. **Use VPC endpoints** (avoid NAT Gateway $32/month)
4. **Implement request throttling** (prevent cost spikes)

### **Monthly Cost Breakdown**
```
Development Environment:
- Bedrock (Haiku): $20-30
- OpenSearch (2 OCU): $350
- Lambda: $5-10
- DynamoDB: $5
- S3: $2
- Other: $10
Total: ~$400/month

Production Environment:
- Bedrock (Sonnet + Haiku): $100-200
- OpenSearch (6 OCU): $1,050
- Lambda: $20-30
- DynamoDB: $20-30
- S3: $10
- CloudFront: $20
- Other: $30
Total: ~$1,250-1,400/month
```

### **Scaling Costs**
| Traffic | Bedrock | OpenSearch | Lambda | Total/month |
|---------|---------|------------|--------|-------------|
| 10K req | $30 | $350 | $5 | ~$400 |
| 100K req | $150 | $700 | $20 | ~$900 |
| 1M req | $800 | $1,400 | $100 | ~$2,500 |

---

## 🔧 Troubleshooting

### **Common Issues**

#### Issue: "Bedrock model not available"
```bash
# Check model access
aws bedrock list-foundation-models --region us-east-1

# Request access if needed (AWS Console)
```

#### Issue: "OpenSearch collection creation failed"
```bash
# Check service quotas
aws service-quotas get-service-quota \
  --service-code aoss \
  --quota-code L-XXXXXXXX

# Request quota increase if needed
```

#### Issue: "Lambda timeout"
```bash
# Increase timeout in Terraform
# variables.tf → lambda_timeout = 600

# Or via CLI
aws lambda update-function-configuration \
  --function-name kass-chatbot-dev-orchestrator \
  --timeout 600
```

#### Issue: "API Gateway 429 (throttled)"
```bash
# Check usage plan limits
aws apigateway get-usage-plan --usage-plan-id xxxxx

# Increase throttle limits in Terraform
# api_throttle_rate_limit = 20000
```

---

## 📊 Monitoring & Alerts

### **Key Metrics to Watch**
1. **API Gateway**: Request count, 4xx/5xx errors, latency (p50/p99)
2. **Lambda**: Invocations, errors, duration, throttles
3. **Bedrock**: API calls, throttles, model latency
4. **OpenSearch**: Search latency, indexing rate
5. **DynamoDB**: Read/write capacity, throttled requests
6. **Cost**: Daily spend, anomalies

### **CloudWatch Logs Insights Queries**

**Lambda errors:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**API latency:**
```
fields @timestamp, latency
| stats avg(latency), max(latency), pct(latency, 95) by bin(5m)
```

**Bedrock usage:**
```
fields @timestamp, model, inputTokens, outputTokens
| stats sum(inputTokens), sum(outputTokens) by model
```

---

## 🎓 Best Practices

### **Development**
- Use `dev` environment for testing
- Keep `prod` environment protected with manual approvals
- Test infrastructure changes in `dev` first
- Use feature flags for gradual rollouts

### **Security**
- Rotate API keys regularly
- Use least-privilege IAM roles
- Enable CloudTrail for audit logs
- Encrypt all data at rest and in transit
- Use Secrets Manager for sensitive data

### **Cost Management**
- Set up billing alarms
- Review cost reports weekly
- Use AWS Cost Explorer for trends
- Tag all resources for cost allocation
- Clean up unused resources

### **Reliability**
- Deploy to multiple AZs
- Implement retries with exponential backoff
- Use circuit breakers for external APIs
- Monitor error rates and latency
- Have runbooks for common issues

---

## 🚨 Rollback Procedure

If deployment fails:

```bash
# Rollback to previous Terraform state
terraform state pull > state-backup.json
terraform apply -var-file=environments/dev/terraform.tfvars -target=module.xxx

# Or destroy and recreate
terraform destroy -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# Restore data from backups
aws dynamodb restore-table-from-backup \
  --target-table-name kass-conversations-dev \
  --backup-arn arn:aws:dynamodb:...
```

---

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [OpenSearch Serverless Guide](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Cost Optimization Guide](https://aws.amazon.com/architecture/well-architected/)

---

## ✅ Success Criteria

Migration is complete when:
- [ ] All infrastructure deployed via Terraform
- [ ] All data migrated from local to AWS
- [ ] API Gateway accessible and working
- [ ] All Lambda functions tested
- [ ] Vector search working with OpenSearch
- [ ] Conversations stored in DynamoDB
- [ ] Monitoring and alarms configured
- [ ] CI/CD pipeline operational
- [ ] Documentation complete
- [ ] Team trained on new architecture

---

**Estimated Migration Time**: 7-10 days
**Team Size**: 2-3 engineers
**Downtime**: Zero (parallel deployment, switch DNS)
