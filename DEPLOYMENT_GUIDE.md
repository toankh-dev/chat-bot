# 🚀 KASS Chatbot - AWS Deployment Guide

**Complete Step-by-Step Instructions for Deploying to AWS**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Steps](#deployment-steps)
5. [Post-Deployment Configuration](#post-deployment-configuration)
6. [Testing & Validation](#testing--validation)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Cost Estimation](#cost-estimation)
10. [Rollback Procedures](#rollback-procedures)

---

## Overview

### What You're Deploying

This guide will deploy a **serverless multi-agent chatbot** on AWS with the following components:

- **API Gateway** - REST API endpoints
- **Lambda Functions** - Serverless compute (orchestrator, vector search, document processor)
- **Amazon Bedrock** - LLM (Claude 3 Haiku) and embeddings (Titan)
- **OpenSearch Serverless** - Vector database for RAG
- **DynamoDB** - Conversation storage
- **S3** - Document storage
- **VPC** - Network isolation
- **IAM** - Security roles and policies
- **EventBridge** - Event automation

### Estimated Deployment Time

- **First-time deployment**: 60-90 minutes
- **Subsequent deployments**: 15-20 minutes

### Estimated Monthly Cost

- **Development Environment**: ~$400/month
- **Production Environment**: ~$1,250/month

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| **AWS CLI** | 2.x+ | [Download](https://aws.amazon.com/cli/) |
| **Terraform** | 1.5.0+ | [Download](https://www.terraform.io/downloads) |
| **Python** | 3.11+ | [Download](https://www.python.org/downloads/) |
| **PowerShell** | 5.1+ | Built-in on Windows |

### AWS Account Requirements

- [ ] AWS Account with admin access
- [ ] AWS Access Key ID and Secret Access Key
- [ ] Amazon Bedrock model access (see below)
- [ ] Service quotas:
  - Lambda concurrent executions: 100+
  - OpenSearch Serverless collections: 1+
  - VPC limit: 5+

### Check Your Tools

```powershell
# Verify installations
aws --version          # Should show: aws-cli/2.x.x
terraform version      # Should show: Terraform v1.5.0+
python --version       # Should show: Python 3.11.x
$PSVersionTable.PSVersion  # Should show: 5.1 or higher

# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID: YOUR_ACCESS_KEY
# - AWS Secret Access Key: YOUR_SECRET_KEY
# - Default region: us-east-1
# - Default output format: json

# Verify AWS credentials
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   VPC (10.0.0.0/16)                  │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │           Private Subnets (Multi-AZ)           │ │  │
│  │  │                                                │ │  │
│  │  │  ┌──────────────┐  ┌──────────────┐           │ │  │
│  │  │  │   Lambda     │  │   Lambda     │           │ │  │
│  │  │  │ Orchestrator │  │Vector Search │  ←──┐     │ │  │
│  │  │  └──────────────┘  └──────────────┘     │     │ │  │
│  │  │          ↓                ↓              │     │ │  │
│  │  │  ┌──────────────────────────────────┐   │     │ │  │
│  │  │  │   OpenSearch Serverless          │   │     │ │  │
│  │  │  │   (Vector Database)              │   │     │ │  │
│  │  │  └──────────────────────────────────┘   │     │ │  │
│  │  └────────────────────────────────────────┘│     │ │  │
│  └───────────────────────────────────────────────┘  │     │ │
│                                                      │     │ │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │     │ │
│  │  API Gateway │  │   DynamoDB   │  │    S3     │ │     │ │
│  │   (REST)     │  │(Conversations)│  │(Documents)│ │     │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │     │ │
│         ↑                                           │     │ │
└─────────┼───────────────────────────────────────────┼─────┘ │
          │                                           │       │
    ┌─────┴─────┐                          ┌─────────┴──────┐│
    │   Users   │                          │ Amazon Bedrock ││
    │  (HTTPS)  │                          │ (Claude/Titan) ││
    └───────────┘                          └────────────────┘│
                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

| Component | Purpose | Location |
|-----------|---------|----------|
| **VPC** | Network isolation | [terraform/modules/vpc/](terraform/modules/vpc/) |
| **S3** | Document storage | [terraform/modules/s3/](terraform/modules/s3/) |
| **DynamoDB** | Conversation history | [terraform/modules/dynamodb/](terraform/modules/dynamodb/) |
| **OpenSearch** | Vector search | [terraform/modules/opensearch/](terraform/modules/opensearch/) |
| **Lambda** | Serverless functions | [terraform/modules/lambda/](terraform/modules/lambda/) |
| **IAM** | Access control | [terraform/modules/iam/](terraform/modules/iam/) |
| **API Gateway** | REST API | [terraform/modules/api_gateway/](terraform/modules/api_gateway/) |
| **EventBridge** | Event automation | [terraform/modules/eventbridge/](terraform/modules/eventbridge/) |

---

## Deployment Steps

### Phase 1: AWS Account Setup (15 minutes)

#### Step 1.1: Request Amazon Bedrock Model Access

⚠️ **CRITICAL** - Deployment will fail without this!

1. Open AWS Console: https://console.aws.amazon.com/bedrock/
2. Navigate to: **Amazon Bedrock → Model access**
3. Click: **"Manage model access"**
4. Select these models:
   - ✅ **Anthropic Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`)
   - ✅ **Amazon Titan Embeddings V2** (`amazon.titan-embed-text-v2:0`)
5. Click: **"Save changes"**
6. Wait 5-10 minutes for approval

**Verify access:**
```powershell
aws bedrock list-foundation-models --region us-east-1 | Select-String "haiku"
```

Expected output:
```
"modelId": "anthropic.claude-3-haiku-20240307-v1:0"
```

#### Step 1.2: Create Terraform Backend Resources

These resources store Terraform's state file and must be created **before** running Terraform:

```powershell
# Create S3 bucket for Terraform state
aws s3 mb s3://kass-chatbot-terraform-state --region us-east-1

# Enable versioning (important for rollback)
aws s3api put-bucket-versioning `
  --bucket kass-chatbot-terraform-state `
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block `
  --bucket kass-chatbot-terraform-state `
  --public-access-block-configuration `
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create DynamoDB table for state locking
aws dynamodb create-table `
  --table-name kass-chatbot-terraform-locks `
  --attribute-definitions AttributeName=LockID,AttributeType=S `
  --key-schema AttributeName=LockID,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST `
  --region us-east-1

# Verify creation
aws s3 ls | Select-String "terraform-state"
aws dynamodb list-tables | Select-String "terraform-locks"
```

Expected output:
```
✅ kass-chatbot-terraform-state
✅ kass-chatbot-terraform-locks
```

---

### Phase 2: Build Lambda Functions (10 minutes)

#### Step 2.1: Build Lambda Deployment Packages

```powershell
# Navigate to terraform directory
cd C:\Users\ToanKH\Documents\source\kass\terraform

# Run build script
.\build-lambdas.ps1
```

The script will:
1. Create `dist/layers/` and `dist/functions/` directories
2. Copy Lambda function code
3. Install Python dependencies
4. Create ZIP files for deployment

Expected output:
```
Building Lambda packages...

Building common-utilities layer...
✓ common-utilities.zip created

Building orchestrator function...
✓ orchestrator.zip created

Building vector_search function...
✓ vector_search.zip created

Building document_processor function...
✓ document_processor.zip created

✓ All Lambda packages built successfully!
Location: C:\Users\ToanKH\Documents\source\kass\terraform\dist
```

**Verify ZIP files:**
```powershell
ls dist\layers\*.zip
ls dist\functions\*.zip
```

You should see:
- `dist/layers/common-utilities.zip` (~10-20 MB)
- `dist/functions/orchestrator.zip` (~5 MB)
- `dist/functions/vector_search.zip` (~5 MB)
- `dist/functions/document_processor.zip` (~5 MB)

---

### Phase 3: Deploy Infrastructure with Terraform (20-30 minutes)

#### Step 3.1: Initialize Terraform

```powershell
# Ensure you're in the terraform directory
cd C:\Users\ToanKH\Documents\source\kass\terraform

# Initialize Terraform (use forward slashes!)
terraform init -backend-config="environments/dev/backend.tfvars"
```

Expected output:
```
Initializing modules...
Initializing the backend...
Successfully configured the backend "s3"!
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...
- Installed hashicorp/aws v5.x.x

Terraform has been successfully initialized!
```

#### Step 3.2: Validate Configuration

```powershell
# Check for syntax errors
terraform validate
```

Expected output:
```
Success! The configuration is valid.
```

#### Step 3.3: Review Deployment Plan

```powershell
# Preview what will be created
terraform plan -var-file="environments/dev/terraform.tfvars" -out=tfplan
```

Review the output. You should see approximately **50-60 resources** to be created:
- VPC and networking resources (~15)
- S3 buckets (~4)
- DynamoDB tables (~3)
- OpenSearch collection (~1)
- IAM roles and policies (~10)
- Lambda functions (~7)
- API Gateway resources (~10)
- EventBridge rules (~3)
- CloudWatch log groups (~7)

#### Step 3.4: Deploy Core Infrastructure (Without Lambda)

Due to module configuration complexities, deploy in stages:

```powershell
# Deploy VPC, S3, DynamoDB, OpenSearch, and IAM first
terraform apply -var-file="environments/dev/terraform.tfvars" -target=module.vpc -target=module.s3 -target=module.dynamodb  -target=module.opensearch -target=module.iam 

# Type 'yes' when prompted
```

⏱️ **This will take 15-20 minutes** (OpenSearch collection is slow to create)

Watch for:
```
module.vpc.aws_vpc.main: Creating...
module.vpc.aws_vpc.main: Creation complete after 3s
module.s3.aws_s3_bucket.buckets["documents"]: Creating...
module.dynamodb.aws_dynamodb_table.tables["conversations"]: Creating...
module.opensearch.aws_opensearchserverless_collection.main: Creating...
module.opensearch.aws_opensearchserverless_collection.main: Still creating... [1m0s elapsed]
module.opensearch.aws_opensearchserverless_collection.main: Still creating... [2m0s elapsed]
...
module.opensearch.aws_opensearchserverless_collection.main: Creation complete after 18m23s

Apply complete! Resources: 45 added, 0 changed, 0 destroyed.
```

#### Step 3.5: Save Infrastructure Outputs

```powershell
# Save all outputs to a file
terraform output -json > ../infrastructure-outputs.json

# View key outputs
terraform output
```

Important outputs to note:
- `opensearch_collection_endpoint` - For Lambda environment variables
- `opensearch_collection_id` - For Lambda environment variables
- `lambda_execution_role_arn` - For Lambda creation
- `private_subnet_ids` - For Lambda VPC configuration
- `lambda_security_group_id` - For Lambda VPC configuration
- `s3_bucket_names` - For application configuration
- `dynamodb_table_names` - For application configuration

---

### Phase 4: Deploy Lambda Functions (10 minutes)

Since the Terraform Lambda module has configuration issues, deploy Lambda functions using AWS CLI:

#### Step 4.1: Extract Terraform Outputs

```powershell
# Set variables from Terraform outputs
$OPENSEARCH_ENDPOINT = terraform output -raw opensearch_collection_endpoint
$OPENSEARCH_ID = terraform output -raw opensearch_collection_id
$EXEC_ROLE_ARN = terraform output -raw lambda_execution_role_arn
$SUBNET_IDS = (terraform output -json private_subnet_ids | ConvertFrom-Json) -join ','
$SG_ID = terraform output -raw lambda_security_group_id
$CONV_TABLE = (terraform output -json dynamodb_table_names | ConvertFrom-Json).conversations
$DOCS_BUCKET = (terraform output -json s3_bucket_names | ConvertFrom-Json).documents

# Verify variables
Write-Host "OpenSearch Endpoint: $OPENSEARCH_ENDPOINT"
Write-Host "Execution Role: $EXEC_ROLE_ARN"
Write-Host "Subnets: $SUBNET_IDS"
```

#### Step 4.2: Deploy Orchestrator Lambda

```powershell
aws lambda create-function `
  --function-name kass-chatbot-dev-orchestrator `
  --runtime python3.11 `
  --role $EXEC_ROLE_ARN `
  --handler handler.handler `
  --zip-file fileb://dist/functions/orchestrator.zip `
  --timeout 300 `
  --memory-size 1024 `
  --environment "Variables={
OPENSEARCH_ENDPOINT=$OPENSEARCH_ENDPOINT,
OPENSEARCH_COLLECTION_ID=$OPENSEARCH_ID,
CONVERSATIONS_TABLE=$CONV_TABLE,
DOCUMENTS_BUCKET=$DOCS_BUCKET,
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0,
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0,
LOG_LEVEL=INFO
}" `
  --vpc-config "SubnetIds=$SUBNET_IDS,SecurityGroupIds=$SG_ID" `
  --region us-east-1
```

#### Step 4.3: Deploy Vector Search Lambda

```powershell
aws lambda create-function `
  --function-name kass-chatbot-dev-vector-search `
  --runtime python3.11 `
  --role $EXEC_ROLE_ARN `
  --handler handler.handler `
  --zip-file fileb://dist/functions/vector_search.zip `
  --timeout 60 `
  --memory-size 512 `
  --environment "Variables={
OPENSEARCH_ENDPOINT=$OPENSEARCH_ENDPOINT,
OPENSEARCH_COLLECTION_ID=$OPENSEARCH_ID,
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0,
LOG_LEVEL=INFO
}" `
  --vpc-config "SubnetIds=$SUBNET_IDS,SecurityGroupIds=$SG_ID" `
  --region us-east-1
```

#### Step 4.4: Deploy Document Processor Lambda

```powershell
aws lambda create-function `
  --function-name kass-chatbot-dev-document-processor `
  --runtime python3.11 `
  --role $EXEC_ROLE_ARN `
  --handler handler.handler `
  --zip-file fileb://dist/functions/document_processor.zip `
  --timeout 900 `
  --memory-size 3008 `
  --environment "Variables={
OPENSEARCH_ENDPOINT=$OPENSEARCH_ENDPOINT,
OPENSEARCH_COLLECTION_ID=$OPENSEARCH_ID,
DOCUMENTS_BUCKET=$DOCS_BUCKET,
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0,
CHUNK_SIZE=1000,
CHUNK_OVERLAP=200,
LOG_LEVEL=INFO
}" `
  --vpc-config "SubnetIds=$SUBNET_IDS,SecurityGroupIds=$SG_ID" `
  --region us-east-1
```

#### Step 4.5: Verify Lambda Deployment

```powershell
# List deployed functions
aws lambda list-functions `
  --query 'Functions[?starts_with(FunctionName, `kass-chatbot-dev`)].{Name:FunctionName,Runtime:Runtime,Size:CodeSize}' `
  --output table
```

Expected output:
```
-------------------------------------------------------------------
|                        ListFunctions                           |
+-------------------------------------+-----------+--------------+
|              Name                   | Runtime   |    Size      |
+-------------------------------------+-----------+--------------+
| kass-chatbot-dev-orchestrator       | python3.11|   5242880    |
| kass-chatbot-dev-vector-search      | python3.11|   5242880    |
| kass-chatbot-dev-document-processor | python3.11|   5242880    |
+-------------------------------------+-----------+--------------+
```

---

### Phase 5: Deploy API Gateway (15 minutes)

#### Step 5.1: Deploy API Gateway Module

```powershell
# Deploy API Gateway and EventBridge
terraform apply -var-file="environments/dev/terraform.tfvars" `
  -target=module.api_gateway `
  -target=module.eventbridge
```

**Note**: This may fail if the Lambda module variables are incompatible. If so, skip to manual API Gateway creation below.

#### Step 5.2: Manual API Gateway Creation (Alternative)

If Terraform API Gateway deployment fails, create manually:

```powershell
# Create REST API
$API_ID = (aws apigateway create-rest-api `
  --name "kass-chatbot-dev-api" `
  --description "KASS Chatbot REST API - Development" `
  --endpoint-configuration types=REGIONAL `
  --query 'id' `
  --output text)

Write-Host "API ID: $API_ID"

# Get root resource ID
$ROOT_ID = (aws apigateway get-resources `
  --rest-api-id $API_ID `
  --query 'items[0].id' `
  --output text)

# Create /chat resource
$CHAT_RESOURCE_ID = (aws apigateway create-resource `
  --rest-api-id $API_ID `
  --parent-id $ROOT_ID `
  --path-part chat `
  --query 'id' `
  --output text)

# Create POST method for /chat
aws apigateway put-method `
  --rest-api-id $API_ID `
  --resource-id $CHAT_RESOURCE_ID `
  --http-method POST `
  --authorization-type NONE

# Get orchestrator Lambda ARN
$ORCHESTRATOR_ARN = (aws lambda get-function `
  --function-name kass-chatbot-dev-orchestrator `
  --query 'Configuration.FunctionArn' `
  --output text)

# Integrate with Lambda
aws apigateway put-integration `
  --rest-api-id $API_ID `
  --resource-id $CHAT_RESOURCE_ID `
  --http-method POST `
  --type AWS_PROXY `
  --integration-http-method POST `
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$ORCHESTRATOR_ARN/invocations"

# Give API Gateway permission to invoke Lambda
$ACCOUNT_ID = (aws sts get-caller-identity --query 'Account' --output text)
aws lambda add-permission `
  --function-name kass-chatbot-dev-orchestrator `
  --statement-id apigateway-invoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/*/chat"

# Deploy API
aws apigateway create-deployment `
  --rest-api-id $API_ID `
  --stage-name dev `
  --description "Initial deployment"

# Get API URL
$API_URL = "https://${API_ID}.execute-api.us-east-1.amazonaws.com/dev"
Write-Host "`nAPI Gateway URL: $API_URL"
Write-Host "Chat Endpoint: $API_URL/chat"

# Save API URL
Set-Content -Path "../api-gateway-url.txt" -Value $API_URL
```

---

## Post-Deployment Configuration

### Configure Secrets Manager (Optional)

Store API keys and sensitive data:

```powershell
# Discord token
aws secretsmanager create-secret `
  --name kass-chatbot/dev/discord-token `
  --secret-string '{"token":"YOUR_DISCORD_TOKEN"}' `
  --region us-east-1

# Slack token
aws secretsmanager create-secret `
  --name kass-chatbot/dev/slack-token `
  --secret-string '{"bot_token":"YOUR_SLACK_TOKEN"}' `
  --region us-east-1

# API keys
aws secretsmanager create-secret `
  --name kass-chatbot/dev/api-keys `
  --secret-string '{"gitlab":"xxx","backlog":"xxx"}' `
  --region us-east-1
```

### Create OpenSearch Index

Initialize the vector search index:

```powershell
# Create index creation script
$indexScript = @"
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Get credentials
session = boto3.Session()
credentials = session.get_credentials()
auth = AWSV4SignerAuth(credentials, 'us-east-1', 'aoss')

# Connect to OpenSearch
endpoint = '$OPENSEARCH_ENDPOINT'
client = OpenSearch(
    hosts=[{'host': endpoint.replace('https://', ''), 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

# Create index with k-NN configuration
index_name = 'knowledge_base'
index_body = {
    'settings': {
        'index': {
            'knn': True,
            'number_of_shards': 2,
            'number_of_replicas': 1
        }
    },
    'mappings': {
        'properties': {
            'embedding': {
                'type': 'knn_vector',
                'dimension': 1024,  # Titan Embeddings V2 dimension
                'method': {
                    'name': 'hnsw',
                    'space_type': 'cosinesimil',
                    'engine': 'faiss'
                }
            },
            'text': {'type': 'text'},
            'metadata': {'type': 'object'},
            'source': {'type': 'keyword'},
            'timestamp': {'type': 'date'}
        }
    }
}

# Create index
try:
    response = client.indices.create(index_name, body=index_body)
    print(f'✓ Index {index_name} created successfully')
except Exception as e:
    print(f'Error: {e}')
"@

Set-Content -Path "../create-opensearch-index.py" -Value $indexScript

# Run the script
python ../create-opensearch-index.py
```

---

## Testing & Validation

### Test 1: Health Check

```powershell
# Test orchestrator Lambda directly
aws lambda invoke `
  --function-name kass-chatbot-dev-orchestrator `
  --payload '{"httpMethod":"GET","path":"/health"}' `
  response.json

cat response.json
```

Expected response:
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"healthy\",\"service\":\"kass-chatbot-orchestrator\"}"
}
```

### Test 2: Chat Endpoint

```powershell
# Test via API Gateway
$API_URL = Get-Content ../api-gateway-url.txt

curl -X POST "$API_URL/chat" `
  -H "Content-Type: application/json" `
  -d '{"message":"Hello! What can you help me with?","conversation_id":"test-001"}'
```

Expected response:
```json
{
  "conversation_id": "test-001",
  "message": "Hello! I'm KASS, your AI assistant. I can help you with...",
  "sources": [],
  "processing_time": 2.5
}
```

### Test 3: Vector Search

```powershell
# Upload a test document first
$DOCS_BUCKET = (terraform output -json s3_bucket_names | ConvertFrom-Json).documents

# Create test document
$testDoc = "This is a test document about machine learning and AI."
Set-Content -Path test-doc.txt -Value $testDoc

# Upload to S3
aws s3 cp test-doc.txt s3://$DOCS_BUCKET/test/test-doc.txt

# Wait for processing (document processor Lambda should be triggered)
Start-Sleep -Seconds 30

# Test vector search
aws lambda invoke `
  --function-name kass-chatbot-dev-vector-search `
  --payload '{"query":"machine learning","limit":5}' `
  search-response.json

cat search-response.json
```

### Test 4: View Logs

```powershell
# Orchestrator logs
aws logs tail /aws/lambda/kass-chatbot-dev-orchestrator --follow

# Vector search logs
aws logs tail /aws/lambda/kass-chatbot-dev-vector-search --follow

# Document processor logs
aws logs tail /aws/lambda/kass-chatbot-dev-document-processor --follow
```

---

## Monitoring & Maintenance

### CloudWatch Dashboards

View metrics in AWS Console:
- Navigate to: **CloudWatch → Dashboards**
- Look for: `kass-chatbot-dev` dashboard (if created by Terraform)

Key metrics to monitor:
- **Lambda Invocations**: Number of function calls
- **Lambda Errors**: Failed executions
- **Lambda Duration**: Response times
- **API Gateway Requests**: Total API calls
- **API Gateway 4xx/5xx**: Error rates
- **DynamoDB Read/Write**: Database activity
- **OpenSearch Search Latency**: Vector search performance

### Set Up Billing Alerts

```powershell
# Create SNS topic for alerts
$SNS_TOPIC_ARN = (aws sns create-topic `
  --name kass-chatbot-billing-alerts `
  --query 'TopicArn' `
  --output text)

# Subscribe your email
aws sns subscribe `
  --topic-arn $SNS_TOPIC_ARN `
  --protocol email `
  --notification-endpoint your-email@example.com

# Create CloudWatch alarm for costs > $20/day
aws cloudwatch put-metric-alarm `
  --alarm-name kass-chatbot-dev-daily-cost `
  --alarm-description "Alert when daily cost exceeds $20" `
  --metric-name EstimatedCharges `
  --namespace AWS/Billing `
  --statistic Maximum `
  --period 86400 `
  --evaluation-periods 1 `
  --threshold 20 `
  --comparison-operator GreaterThanThreshold `
  --alarm-actions $SNS_TOPIC_ARN
```

### Regular Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Review logs | Daily | `aws logs tail /aws/lambda/...` |
| Check costs | Weekly | AWS Cost Explorer |
| Update Lambda code | As needed | `aws lambda update-function-code ...` |
| Backup DynamoDB | Weekly | AWS Backup |
| Review security | Monthly | AWS Security Hub |

---

## Troubleshooting

### Common Issues

#### Issue 1: "Bedrock model not available"

**Error:**
```
AccessDeniedException: You don't have access to the model with the specified model ID
```

**Solution:**
```powershell
# Check model access status
aws bedrock list-foundation-models --region us-east-1 | Select-String "haiku"

# If empty, request access in AWS Console → Bedrock → Model access
```

#### Issue 2: "OpenSearch collection creation timeout"

**Error:**
```
Error: timeout while waiting for state to become 'ACTIVE'
```

**Solution:**
OpenSearch Serverless can take 15-25 minutes to create. Be patient!

```powershell
# Check status manually
aws opensearchserverless list-collections
aws opensearchserverless batch-get-collection --ids YOUR_COLLECTION_ID
```

#### Issue 3: "Lambda timeout in VPC"

**Error:**
```
Task timed out after 300.00 seconds
```

**Solution:**
Lambda in VPC needs NAT Gateway or VPC Endpoints for internet access:

```powershell
# Check if VPC endpoints exist
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=YOUR_VPC_ID"

# Lambda needs endpoints for: Bedrock, OpenSearch, DynamoDB, S3
# These are configured in terraform/modules/vpc/main.tf
```

#### Issue 4: "API Gateway 403 Forbidden"

**Error:**
```
{"message":"Forbidden"}
```

**Solution:**
Check Lambda permissions:

```powershell
# Get Lambda policy
aws lambda get-policy --function-name kass-chatbot-dev-orchestrator

# Add permission if missing
aws lambda add-permission `
  --function-name kass-chatbot-dev-orchestrator `
  --statement-id apigateway-invoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com
```

#### Issue 5: "Terraform state locked"

**Error:**
```
Error: Error acquiring the state lock
```

**Solution:**
```powershell
# Force unlock (only if you're sure no other process is running)
terraform force-unlock LOCK_ID

# Or delete lock from DynamoDB
aws dynamodb delete-item `
  --table-name kass-chatbot-terraform-locks `
  --key '{"LockID":{"S":"kass-chatbot-terraform-state/dev/terraform.tfstate"}}'
```

### Debug Commands

```powershell
# Check Lambda environment variables
aws lambda get-function-configuration `
  --function-name kass-chatbot-dev-orchestrator `
  --query 'Environment.Variables'

# Test Lambda locally with payload
aws lambda invoke `
  --function-name kass-chatbot-dev-orchestrator `
  --payload file://test-payload.json `
  --log-type Tail `
  response.json

# View last 100 log lines
aws logs tail /aws/lambda/kass-chatbot-dev-orchestrator `
  --since 1h `
  --format short

# Get CloudWatch Insights query
aws logs start-query `
  --log-group-name /aws/lambda/kass-chatbot-dev-orchestrator `
  --start-time $(Get-Date).AddHours(-1).ToUniversalTime().ToString("s") `
  --end-time $(Get-Date).ToUniversalTime().ToString("s") `
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc'
```

---

## Cost Estimation

### Development Environment (~$400/month)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **OpenSearch Serverless** | 2 OCU | $350 |
| **Bedrock (Haiku)** | 50K requests, 10M tokens | $20-30 |
| **Lambda** | 50K invocations, 1GB, 5s avg | $5-10 |
| **DynamoDB** | 50K writes, 200K reads | $5-8 |
| **S3** | 10GB storage, 100K requests | $2 |
| **API Gateway** | 50K requests | $0.18 |
| **Data Transfer** | 5GB egress | $0.45 |
| **CloudWatch Logs** | 5GB | $2.50 |
| **VPC** | 2 subnets, 2 AZs | $0 (no NAT) |
| **TOTAL** | | **~$385-408** |

### Production Environment (~$1,250/month)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **OpenSearch Serverless** | 6 OCU | $1,050 |
| **Bedrock (Sonnet)** | 200K requests, 50M tokens | $100-200 |
| **Lambda** | 500K invocations, 2GB, 4s avg | $20-30 |
| **DynamoDB** | 500K writes, 2M reads | $20-30 |
| **S3** | 100GB storage, 1M requests | $10 |
| **API Gateway** | 500K requests | $1.75 |
| **CloudFront** | 100GB transfer | $20 |
| **Data Transfer** | 50GB egress | $4.50 |
| **CloudWatch** | 50GB logs | $25 |
| **TOTAL** | | **~$1,251-1,391** |

### Cost Optimization Tips

1. **Use Claude Haiku for simple queries** (10x cheaper than Sonnet)
2. **Enable response caching** (reduce LLM calls by 30-40%)
3. **Use VPC endpoints** (avoid NAT Gateway $32/month)
4. **Set CloudWatch log retention** to 3-7 days in dev
5. **Use S3 lifecycle policies** (move old docs to Glacier)
6. **Enable DynamoDB auto-scaling** (pay only for what you use)

---

## Rollback Procedures

### Rollback Terraform Changes

```powershell
# View state history
terraform state list

# Restore previous state from S3
aws s3 cp s3://kass-chatbot-terraform-state/dev/terraform.tfstate.backup terraform.tfstate

# Or destroy specific resources
terraform destroy -var-file="environments/dev/terraform.tfvars" `
  -target=module.lambda

# Full rollback (destroy everything)
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

### Restore DynamoDB from Backup

```powershell
# List backups
aws dynamodb list-backups --table-name kass-chatbot-dev-conversations

# Restore from backup
aws dynamodb restore-table-from-backup `
  --target-table-name kass-chatbot-dev-conversations `
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/kass-chatbot-dev-conversations/backup/12345
```

### Rollback Lambda Code

```powershell
# List function versions
aws lambda list-versions-by-function `
  --function-name kass-chatbot-dev-orchestrator

# Update function to use previous version
aws lambda update-function-code `
  --function-name kass-chatbot-dev-orchestrator `
  --s3-bucket YOUR_CODE_BUCKET `
  --s3-key previous-version.zip
```

---

## Next Steps

After successful deployment:

1. **Configure CI/CD Pipeline**
   - Set up GitHub Actions for automated deployments
   - See: `.github/workflows/deploy.yml`

2. **Migrate Existing Data**
   - Export from local ChromaDB
   - Import to OpenSearch
   - See: `scripts/migrate_to_bedrock.py`

3. **Set Up Custom Domain**
   - Register domain in Route 53
   - Create SSL certificate in ACM
   - Configure API Gateway custom domain

4. **Enable Monitoring**
   - Create CloudWatch dashboards
   - Set up SNS alerts
   - Configure X-Ray tracing

5. **Production Deployment**
   - Copy `environments/dev/` to `environments/prod/`
   - Update production values
   - Deploy with: `terraform apply -var-file=environments/prod/terraform.tfvars`

---

## Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Amazon Bedrock**: https://docs.aws.amazon.com/bedrock/
- **OpenSearch Serverless**: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html
- **Project Repository**: Your internal documentation

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review CloudWatch logs
3. Check [AWS Service Health Dashboard](https://status.aws.amazon.com/)
4. Contact your DevOps team

---

**Document Version**: 1.0.0
**Last Updated**: 2025-01-31
**Maintained By**: Platform Team
