# KASS Chatbot - AWS Implementation Roadmap

## 🎯 Overview

This roadmap outlines the step-by-step implementation plan for completing the AWS migration of the KASS Chatbot system.

**Current Status**: 65% Complete ✅
**Updated**: 2025-01-31
**Next Milestone**: Complete Infrastructure (Week 1-2)

---

## 📊 Current Progress Summary

### ✅ **Completed (65%)**
- [x] ✅ AWS architecture design and documentation (7 docs, 14,000+ lines)
- [x] ✅ Main Terraform configuration ([main.tf](terraform/main.tf), [variables.tf](terraform/variables.tf))
- [x] ✅ VPC Terraform module (complete with all features)
- [x] ✅ S3 Terraform module (complete with lifecycle policies)
- [x] ✅ DynamoDB Terraform module (complete with GSI, TTL, streams)
- [x] ✅ Bedrock client implementation ([bedrock_client.py](lambda_functions/common/bedrock_client.py) - 400 lines)
- [x] ✅ OpenSearch client implementation ([opensearch_client.py](lambda_functions/common/opensearch_client.py) - 500 lines)
- [x] ✅ DynamoDB client implementation ([dynamodb_client.py](lambda_functions/common/dynamodb_client.py) - 400 lines)
- [x] ✅ S3 client implementation ([s3_client.py](lambda_functions/common/s3_client.py) - 400 lines)
- [x] ✅ Lambda orchestrator handler ([handler.py](lambda_functions/orchestrator/handler.py) - 300 lines)
- [x] ✅ Requirements files for Lambda functions
- [x] ✅ Dev environment configuration

### 🔄 **In Progress (20%)**
- [ ] IAM Terraform module (structure defined, needs policies)
- [ ] OpenSearch Terraform module (structure defined)
- [ ] Lambda Terraform module (structure defined)
- [ ] API Gateway Terraform module (structure defined)
- [ ] EventBridge Terraform module (structure defined)

### 📅 **Pending (15%)**
- [ ] Remaining Lambda functions (vector_search, document_processor, tools)
- [ ] Migration scripts (export/import data)
- [ ] Build and deployment scripts
- [ ] Testing suite (unit, integration, load)
- [ ] Monitoring setup (dashboards, alarms)
- [ ] CI/CD pipeline
- [ ] Production deployment

---

## 📅 Updated Implementation Schedule

### **Phase 1: Complete Infrastructure** (Week 1-2, Priority: CRITICAL)

#### **Day 1-2: IAM Module** ⚡ START HERE
**File**: `terraform/modules/iam/main.tf`
**Status**: Structure exists in main.tf, needs full implementation

**What to Create**:
```hcl
# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.name_prefix}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach AWS managed policies
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Custom policy for Bedrock
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.name_prefix}-bedrock-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${var.region}::foundation-model/*"
      }
    ]
  })
}

# Custom policy for OpenSearch
resource "aws_iam_role_policy" "opensearch_access" {
  name = "${var.name_prefix}-opensearch-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn
      }
    ]
  })
}

# Custom policy for DynamoDB
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.name_prefix}-dynamodb-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          for arn in var.dynamodb_table_arns : arn
        ]
      }
    ]
  })
}

# Custom policy for S3
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.name_prefix}-s3-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          for arn in var.s3_bucket_arns : [
            arn,
            "${arn}/*"
          ]
        ]
      }
    ]
  })
}

# API Gateway Role
resource "aws_iam_role" "api_gateway" {
  name = "${var.name_prefix}-api-gateway"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
    }]
  })
}

# EventBridge Role
resource "aws_iam_role" "eventbridge" {
  name = "${var.name_prefix}-eventbridge"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
    }]
  })
}
```

**Also Create**:
- `terraform/modules/iam/variables.tf`
- `terraform/modules/iam/outputs.tf`

**Tasks**:
- [ ] Create IAM module directory structure
- [ ] Implement Lambda execution role with all policies
- [ ] Create API Gateway role
- [ ] Create EventBridge role
- [ ] Add variables for ARNs
- [ ] Add outputs for role ARNs
- [ ] Test role creation

**Estimated Time**: 8-10 hours

**Validation**:
```bash
cd terraform
terraform plan -target=module.iam -var-file=environments/dev/terraform.tfvars
terraform apply -target=module.iam -var-file=environments/dev/terraform.tfvars
```

---

#### **Day 3-4: OpenSearch Serverless Module**
**File**: `terraform/modules/opensearch/main.tf`
**Status**: Structure defined, needs implementation

**What to Create**:
```hcl
# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "main" {
  name = "${var.collection_name}"
  type = var.collection_type  # VECTORSEARCH

  tags = var.tags
}

# Encryption Policy
resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.collection_name}-encryption"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource = ["collection/${var.collection_name}"]
      }
    ],
    AWSOwnedKey = true
  })
}

# Network Policy (VPC access)
resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.collection_name}-network"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = ["collection/${var.collection_name}"]
        },
        {
          ResourceType = "dashboard"
          Resource = ["collection/${var.collection_name}"]
        }
      ],
      AllowFromPublic = false,
      SourceVPCEs = [var.vpc_endpoint_id]
    }
  ])
}

# Data Access Policy
resource "aws_opensearchserverless_access_policy" "data_access" {
  name = "${var.collection_name}-access"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource = ["collection/${var.collection_name}"]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource = ["index/${var.collection_name}/*"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ],
      Principal = var.allowed_principals
    }
  ])
}

# Capacity Settings
resource "aws_opensearchserverless_vpc_endpoint" "main" {
  count = var.create_vpc_endpoint ? 1 : 0

  name       = "${var.name_prefix}-opensearch-vpce"
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  security_group_ids = var.security_group_ids
}
```

**Also Create**:
- `terraform/modules/opensearch/variables.tf`
- `terraform/modules/opensearch/outputs.tf`

**Tasks**:
- [ ] Create OpenSearch module structure
- [ ] Implement collection creation
- [ ] Configure encryption policy
- [ ] Configure network policy (VPC)
- [ ] Configure data access policy
- [ ] Add capacity settings
- [ ] Add outputs (endpoint, collection_id)
- [ ] Test collection creation (takes 10-15 minutes)

**Estimated Time**: 10-12 hours

**Note**: OpenSearch Serverless has minimum 2 OCU cost ($350/month). For dev, consider using `aws_opensearch_domain` with t3.small.search instance ($60/month) instead.

**Validation**:
```bash
terraform apply -target=module.opensearch -var-file=environments/dev/terraform.tfvars
# Wait 10-15 minutes for collection to be active
aws opensearchserverless get-collection --id $(terraform output -raw opensearch_collection_id)
```

---

#### **Day 5-7: Lambda Module**
**File**: `terraform/modules/lambda/main.tf`
**Status**: Structure defined, needs implementation

**What to Create**:
```hcl
# Lambda Functions
resource "aws_lambda_function" "functions" {
  for_each = var.functions

  function_name = "${var.name_prefix}-${each.key}"
  handler       = each.value.handler
  runtime       = each.value.runtime
  role          = var.execution_role_arn

  filename         = "${path.module}/../../dist/${each.key}.zip"
  source_code_hash = filebase64sha256("${path.module}/../../dist/${each.key}.zip")

  memory_size = each.value.memory_size
  timeout     = each.value.timeout

  # VPC Configuration
  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  # Environment Variables
  environment {
    variables = merge(
      var.environment_variables,
      lookup(each.value, "environment", {})
    )
  }

  # Layers
  layers = var.layer_arns

  # Reserved Concurrency (optional)
  reserved_concurrent_executions = lookup(each.value, "reserved_concurrency", -1)

  # Tracing
  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  tags = var.tags
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "functions" {
  for_each = var.functions

  name              = "/aws/lambda/${var.name_prefix}-${each.key}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Lambda Layers
resource "aws_lambda_layer_version" "layers" {
  for_each = { for layer in var.layers : layer.name => layer }

  layer_name          = "${var.name_prefix}-${each.key}"
  filename            = "${path.module}/../../layers/${each.key}.zip"
  source_code_hash    = filebase64sha256("${path.module}/../../layers/${each.key}.zip")
  compatible_runtimes = each.value.compatible_runtimes
  description         = each.value.description
}

# Lambda Permissions for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  for_each = var.functions

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"

  # Allow from any API Gateway in the account
  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:*/*/*/*"
}

# Lambda Permissions for EventBridge
resource "aws_lambda_permission" "eventbridge" {
  for_each = var.functions

  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "events.amazonaws.com"
}
```

**Also Create**:
- `terraform/modules/lambda/variables.tf`
- `terraform/modules/lambda/outputs.tf`

**Tasks**:
- [ ] Create Lambda module structure
- [ ] Implement function resources with dynamic configuration
- [ ] Configure VPC attachment
- [ ] Set up environment variables
- [ ] Create layer resources
- [ ] Add CloudWatch log groups
- [ ] Add permissions for API Gateway and EventBridge
- [ ] Add outputs (function_arns, invoke_arns, layer_arns)
- [ ] Test function creation

**Estimated Time**: 16-20 hours

**Note**: Before applying, you need to create the deployment packages:
```bash
cd lambda_functions
./scripts/package_lambdas.sh  # We'll create this script
```

---

#### **Day 8-9: API Gateway Module**
**File**: `terraform/modules/api_gateway/main.tf`

**What to Create**:
```hcl
# REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = var.api_name
  description = var.api_description

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# Resources and Methods (dynamic)
resource "aws_api_gateway_resource" "resources" {
  for_each = { for k, v in var.lambda_integrations : k => split(" ", k)[1] }

  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = trimprefix(each.value, "/")
}

resource "aws_api_gateway_method" "methods" {
  for_each = var.lambda_integrations

  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.resources[each.key].id
  http_method   = split(" ", each.key)[0]
  authorization = var.enable_cognito_auth ? "COGNITO_USER_POOLS" : "NONE"
  api_key_required = var.enable_api_key_auth
}

# Lambda Integrations
resource "aws_api_gateway_integration" "lambda" {
  for_each = var.lambda_integrations

  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.resources[each.key].id
  http_method = aws_api_gateway_method.methods[each.key].http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = each.value.lambda_invoke_arn
  timeout_milliseconds    = each.value.timeout_milliseconds
}

# Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.main.body))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.lambda
  ]
}

# Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  # Throttling
  throttle_settings {
    burst_limit = var.throttle_burst_limit
    rate_limit  = var.throttle_rate_limit
  }

  # Access Logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format         = "$context.requestId"
  }

  tags = var.tags
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# API Key (if enabled)
resource "aws_api_gateway_api_key" "main" {
  count = var.enable_api_key_auth ? 1 : 0

  name = "${var.api_name}-key"

  tags = var.tags
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "main" {
  count = var.enable_api_key_auth ? 1 : 0

  name = "${var.api_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  throttle_settings {
    burst_limit = var.throttle_burst_limit
    rate_limit  = var.throttle_rate_limit
  }

  tags = var.tags
}

# Usage Plan Key
resource "aws_api_gateway_usage_plan_key" "main" {
  count = var.enable_api_key_auth ? 1 : 0

  key_id        = aws_api_gateway_api_key.main[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main[0].id
}
```

**Tasks**:
- [ ] Create API Gateway module structure
- [ ] Implement REST API resource
- [ ] Create resources and methods dynamically
- [ ] Configure Lambda proxy integrations
- [ ] Set up deployment and stage
- [ ] Configure throttling and logging
- [ ] Add API keys and usage plans
- [ ] Add outputs (api_id, api_url, api_key)
- [ ] Test API endpoints

**Estimated Time**: 12-14 hours

---

#### **Day 10: EventBridge Module**
**File**: `terraform/modules/eventbridge/main.tf`

**What to Create**:
```hcl
# Event Rules
resource "aws_cloudwatch_event_rule" "rules" {
  for_each = var.rules

  name                = "${var.name_prefix}-${each.key}"
  description         = each.value.description
  event_pattern       = lookup(each.value, "event_pattern", null)
  schedule_expression = lookup(each.value, "schedule_expression", null)

  tags = var.tags
}

# Event Targets
resource "aws_cloudwatch_event_target" "targets" {
  for_each = var.rules

  rule      = aws_cloudwatch_event_rule.rules[each.key].name
  target_id = "${each.key}-target"
  arn       = each.value.targets[0].arn

  input = lookup(each.value.targets[0], "input", null)

  # Retry policy
  retry_policy {
    maximum_event_age       = 86400  # 24 hours
    maximum_retry_attempts  = 2
  }

  # Dead letter queue (optional)
  dead_letter_config {
    arn = var.dlq_arn
  }
}

# Lambda Permissions
resource "aws_lambda_permission" "eventbridge" {
  for_each = var.rules

  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.targets[0].arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rules[each.key].arn
}
```

**Tasks**:
- [ ] Create EventBridge module structure
- [ ] Implement event rules with patterns/schedules
- [ ] Configure event targets (Lambda)
- [ ] Add Lambda permissions
- [ ] Add retry policies and DLQ
- [ ] Add outputs (rule_arns)
- [ ] Test event triggering

**Estimated Time**: 6-8 hours

---

### **End of Week 1-2: Infrastructure Complete! 🎉**

**Validation Checklist**:
```bash
# Deploy all modules
cd terraform
terraform init -backend-config=environments/dev/backend.tfvars
terraform plan -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# Verify resources
terraform output

# Test API
export API_URL=$(terraform output -raw api_gateway_url)
export API_KEY=$(terraform output -raw api_gateway_api_key)
curl -H "x-api-key: $API_KEY" $API_URL/health
```

**Expected Output**:
```
✅ VPC created with subnets and security groups
✅ S3 buckets created
✅ DynamoDB tables created
✅ IAM roles created with policies
✅ OpenSearch collection active
✅ Lambda functions deployed
✅ API Gateway endpoints accessible
✅ EventBridge rules configured
```

---

### **Phase 2: Lambda Functions & Scripts** (Week 3, Priority: HIGH)

#### **Day 11: Build Lambda Layers Script**
**File**: `lambda_functions/scripts/build_layers.sh`

```bash
#!/bin/bash
set -e

echo "Building Lambda layers..."

# Create layers directory
mkdir -p layers

# LangChain Layer
echo "Building langchain layer..."
mkdir -p layers/langchain/python
pip install \
    langchain==0.1.0 \
    langchain-community==0.0.10 \
    -t layers/langchain/python
cd layers/langchain
zip -r ../langchain-layer.zip python/
cd ../..

# AWS SDK Layer (boto3)
echo "Building aws-sdk layer..."
mkdir -p layers/aws-sdk/python
pip install \
    boto3==1.34.0 \
    botocore==1.34.0 \
    opensearch-py==2.4.0 \
    requests-aws4auth==1.2.3 \
    -t layers/aws-sdk/python
cd layers/aws-sdk
zip -r ../aws-sdk-layer.zip python/
cd ../..

# Data Processing Layer
echo "Building data-processing layer..."
mkdir -p layers/data-processing/python
pip install \
    pandas==2.0.0 \
    openpyxl==3.1.0 \
    -t layers/data-processing/python
cd layers/data-processing
zip -r ../data-processing-layer.zip python/
cd ../..

echo "✅ All layers built successfully!"
ls -lh layers/*.zip
```

**Tasks**:
- [ ] Create script
- [ ] Make executable (`chmod +x`)
- [ ] Test layer creation
- [ ] Upload to Lambda

**Estimated Time**: 2-3 hours

---

#### **Day 12: Package Lambda Functions Script**
**File**: `lambda_functions/scripts/package_lambdas.sh`

```bash
#!/bin/bash
set -e

echo "Packaging Lambda functions..."

# Create dist directory
mkdir -p dist

# Function list
FUNCTIONS=(
    "orchestrator"
    "vector_search"
    "document_processor"
    "tools/report_tool"
    "tools/summarize_tool"
    "tools/code_review_tool"
    "discord_handler"
)

# Package each function
for func in "${FUNCTIONS[@]}"; do
    echo "Packaging $func..."

    func_name=$(basename $func)

    # Create temp directory
    mkdir -p temp/$func_name

    # Copy function code
    cp -r $func/* temp/$func_name/

    # Copy common utilities
    cp -r common/*.py temp/$func_name/

    # Create zip
    cd temp/$func_name
    zip -r ../../dist/$func_name.zip .
    cd ../..

    # Cleanup
    rm -rf temp/$func_name

    echo "✅ Packaged $func_name"
done

echo "✅ All functions packaged!"
ls -lh dist/*.zip
```

**Tasks**:
- [ ] Create script
- [ ] Make executable
- [ ] Test packaging
- [ ] Verify zip contents

**Estimated Time**: 2-3 hours

---

#### **Day 13-14: Implement Remaining Lambda Functions**

**Vector Search Handler** (`lambda_functions/vector_search/handler.py`):
```python
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchVectorClient

bedrock_client = None
opensearch_client = None

def initialize():
    global bedrock_client, opensearch_client

    bedrock_client = BedrockClient()
    opensearch_client = OpenSearchVectorClient(
        collection_endpoint=os.getenv('OPENSEARCH_ENDPOINT'),
        collection_id=os.getenv('OPENSEARCH_COLLECTION_ID')
    )

def handler(event, context):
    if bedrock_client is None:
        initialize()

    body = json.loads(event['body'])
    query = body['query']
    limit = body.get('limit', 10)

    # Generate embedding
    embeddings = bedrock_client.generate_embeddings([query])
    query_vector = embeddings[0]

    # Search
    results = opensearch_client.search(
        query_vector=query_vector,
        k=limit
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'query': query,
            'results': results,
            'count': len(results)
        })
    }
```

**Document Processor Handler** (`lambda_functions/document_processor/handler.py`):
```python
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchVectorClient
from s3_client import S3Client
import time

bedrock_client = None
opensearch_client = None
s3_client = None

def initialize():
    global bedrock_client, opensearch_client, s3_client

    bedrock_client = BedrockClient()
    opensearch_client = OpenSearchVectorClient(
        collection_endpoint=os.getenv('OPENSEARCH_ENDPOINT')
    )
    s3_client = S3Client()

def handler(event, context):
    if bedrock_client is None:
        initialize()

    # Parse S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Download document
        content = s3_client.get_object(key, bucket)

        # Chunk document
        chunks = chunk_document(content, key)

        # Generate embeddings (batch)
        texts = [chunk['text'] for chunk in chunks]
        embeddings = bedrock_client.generate_embeddings(texts)

        # Index in OpenSearch
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            documents.append({
                'id': f"{key}_{i}",
                'text': chunk['text'],
                'embedding': embedding,
                'metadata': {
                    'source': bucket,
                    'file': key,
                    'chunk_id': i
                },
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            })

        result = opensearch_client.index_documents(documents)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processed',
                'file': key,
                'chunks': len(chunks),
                'indexed': result['indexed']
            })
        }

def chunk_document(content, filename):
    # Simple chunking by paragraphs
    # TODO: Implement better chunking logic
    text = content.decode('utf-8')
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    chunks = []
    for i, para in enumerate(paragraphs):
        if len(para) > 50:  # Skip very short paragraphs
            chunks.append({
                'text': para,
                'metadata': {
                    'chunk_id': i,
                    'filename': filename
                }
            })

    return chunks
```

**Tasks**:
- [ ] Implement vector_search handler
- [ ] Implement document_processor handler
- [ ] Create requirements.txt for each
- [ ] Test locally with sample data
- [ ] Deploy to Lambda

**Estimated Time**: 12-16 hours

---

### **Phase 3: Testing & Migration** (Week 4, Priority: MEDIUM)

#### **Day 15-16: Testing Suite**

**Unit Tests** (`tests/unit/test_bedrock_client.py`):
```python
import pytest
from lambda_functions.common.bedrock_client import BedrockClient

def test_bedrock_initialization():
    client = BedrockClient()
    assert client is not None

def test_generate_embeddings():
    client = BedrockClient()
    texts = ["Hello world", "Test embedding"]
    embeddings = client.generate_embeddings(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) > 0  # Check dimension
```

**Integration Tests** (`tests/integration/test_chat_flow.py`):
```python
import requests
import os

def test_chat_endpoint():
    api_url = os.getenv('API_URL')
    api_key = os.getenv('API_KEY')

    response = requests.post(
        f"{api_url}/chat",
        headers={"x-api-key": api_key},
        json={"message": "Hello!"}
    )

    assert response.status_code == 200
    assert 'answer' in response.json()
```

**Tasks**:
- [ ] Write unit tests for all clients
- [ ] Write integration tests for API endpoints
- [ ] Create test fixtures
- [ ] Set up pytest configuration
- [ ] Run tests and fix issues

**Estimated Time**: 12-16 hours

---

#### **Day 17-18: Migration Scripts**

**Export ChromaDB** (`scripts/export_chromadb.py`):
```python
import chromadb
import json

client = chromadb.HttpClient(host="chromadb", port=8000)
collection = client.get_collection("chatbot_knowledge")

# Get all documents
results = collection.get(include=['documents', 'metadatas'])

# Export to JSON
export_data = []
for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
    export_data.append({
        'text': doc,
        'metadata': metadata
    })

with open('exports/chromadb_vectors.json', 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"Exported {len(export_data)} documents")
```

**Migrate to Bedrock** (`scripts/migrate_to_bedrock.py`):
```python
import json
import boto3
from opensearchpy import OpenSearch, AWSV4SignerAuth

# Load exported data
with open('exports/chromadb_vectors.json', 'r') as f:
    data = json.load(f)

# Initialize Bedrock
bedrock = boto3.client('bedrock-runtime')

# Initialize OpenSearch
# ... (use opensearch_client)

# Process in batches
batch_size = 10
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    texts = [item['text'] for item in batch]

    # Generate embeddings with Bedrock
    # ...

    # Index in OpenSearch
    # ...

    print(f"Processed {i + len(batch)}/{len(data)}")
```

**Tasks**:
- [ ] Create export scripts for ChromaDB and PostgreSQL
- [ ] Create migration scripts to AWS services
- [ ] Add progress tracking and resume capability
- [ ] Test with sample data
- [ ] Document migration procedures

**Estimated Time**: 12-16 hours

---

### **Phase 4: Monitoring & Production** (Week 5-6, Priority: MEDIUM)

#### **Day 19-20: CloudWatch Setup**

**Dashboard** (`monitoring/dashboard.json`):
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum", "label": "API Requests"}],
          [".", "4XXError", {"stat": "Sum", "label": "Client Errors"}],
          [".", "5XXError", {"stat": "Sum", "label": "Server Errors"}],
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Lambda Calls"}],
          [".", "Errors", {"stat": "Sum", "label": "Lambda Errors"}],
          [".", "Duration", {"stat": "Average", "label": "Lambda Duration"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API & Lambda Metrics"
      }
    }
  ]
}
```

**Create Dashboard**:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name kass-chatbot-dev \
  --dashboard-body file://monitoring/dashboard.json
```

**Tasks**:
- [ ] Create CloudWatch dashboard
- [ ] Set up metric alarms
- [ ] Configure SNS notifications
- [ ] Enable X-Ray tracing
- [ ] Test alerting

**Estimated Time**: 8-10 hours

---

#### **Day 21-30: CI/CD & Production**

**GitHub Actions** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy KASS Chatbot

on:
  push:
    branches: [main, develop]

jobs:
  terraform:
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

      - name: Terraform Init
        run: cd terraform && terraform init

      - name: Terraform Apply
        run: cd terraform && terraform apply -auto-approve -var-file=environments/dev/terraform.tfvars

  lambda:
    needs: terraform
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Build Layers
        run: cd lambda_functions && ./scripts/build_layers.sh

      - name: Package Functions
        run: cd lambda_functions && ./scripts/package_lambdas.sh

      - name: Deploy
        run: python scripts/deploy_lambdas.py --environment dev
```

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Set up secrets
- [ ] Test pipeline
- [ ] Deploy to staging
- [ ] Deploy to production

**Estimated Time**: 20-30 hours

---

## 🎯 Summary & Next Actions

### **Immediate Priority (This Week)**:
1. ✅ **Complete IAM Module** (Days 1-2)
2. ✅ **Complete OpenSearch Module** (Days 3-4)
3. ✅ **Complete Lambda Module** (Days 5-7)
4. ✅ **Complete API Gateway Module** (Days 8-9)
5. ✅ **Complete EventBridge Module** (Day 10)

### **Success Criteria**:
- [ ] All Terraform modules implemented
- [ ] Infrastructure deploys successfully
- [ ] API Gateway returns responses
- [ ] Lambda functions execute
- [ ] Vector search works
- [ ] Tests passing
- [ ] Monitoring active
- [ ] CI/CD operational

### **Total Effort Remaining**:
- **Infrastructure**: 60-70 hours
- **Application**: 30-40 hours
- **Testing**: 20-25 hours
- **Migration**: 15-20 hours
- **Production**: 20-30 hours
- **Total**: ~145-185 hours (4-5 weeks with 1 FTE)

---

## 🆘 Getting Help

If you get stuck, refer to:
1. [AWS_ARCHITECTURE.md](AWS_ARCHITECTURE.md) - Architecture details
2. [AWS_MIGRATION_GUIDE.md](AWS_MIGRATION_GUIDE.md) - Deployment procedures
3. [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Current progress
4. [NEXT_STEPS.md](NEXT_STEPS.md) - Quick guidance

---

**Ready to start? Begin with Day 1: IAM Module!** 🚀
