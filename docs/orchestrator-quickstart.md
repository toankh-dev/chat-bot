# 🚀 Multi-Agent Orchestrator - Quick Start Guide

## 📋 Overview

This guide will help you deploy the complete Multi-Agent Orchestrator system in **under 2 hours**.

---

## ⚡ Prerequisites Checklist

```bash
# 1. AWS CLI configured
aws sts get-caller-identity

# 2. Terraform installed
terraform version

# 3. Python 3.11+
python3 --version

# 4. API credentials ready
- GitLab Personal Access Token
- Slack Bot Token
- Backlog API Key
```

---

## 🎯 Deployment Flow

```
Phase 1: Knowledge Base (30 min)
    ↓
Phase 2: Agents Setup (45 min)
    ↓
Phase 3: Testing (15 min)
    ↓
Phase 4: Production Ready (30 min)
```

---

## 📦 Phase 1: Knowledge Base Setup (30 minutes)

### Step 1: Store API Credentials

```bash
# GitLab
aws secretsmanager create-secret \
  --name /chatbot/gitlab/api-token \
  --secret-string '{
    "token": "YOUR_GITLAB_TOKEN",
    "base_url": "https://gitlab.com/api/v4"
  }' \
  --region ap-southeast-1

# Slack
aws secretsmanager create-secret \
  --name /chatbot/slack/bot-token \
  --secret-string '{
    "bot_token": "xoxb-YOUR-SLACK-TOKEN",
    "signing_secret": "YOUR_SIGNING_SECRET"
  }' \
  --region ap-southeast-1

# Backlog
aws secretsmanager create-secret \
  --name /chatbot/backlog/api-key \
  --secret-string '{
    "api_key": "YOUR_BACKLOG_KEY",
    "space_url": "https://YOUR_SPACE.backlog.com"
  }' \
  --region ap-southeast-1
```

### Step 2: Deploy Knowledge Base

```bash
# Clone repository
git clone https://github.com/yourcompany/chatbot-multi-agent.git
cd chatbot-multi-agent

# Deploy Knowledge Base infrastructure
cd terraform/knowledge-base
terraform init
terraform apply -auto-approve

# Save Knowledge Base ID
export KB_ID=$(terraform output -raw knowledge_base_id)
echo "Knowledge Base ID: $KB_ID"
```

### Step 3: Initial Data Ingestion

```bash
# Run data fetcher manually
aws lambda invoke \
  --function-name chatbot-data-fetcher \
  --region ap-southeast-1 \
  response.json

# Check response
cat response.json

# Monitor ingestion job
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $(terraform output -raw data_source_id) \
  --region ap-southeast-1
```

---

## 🤖 Phase 2: Agents Setup (45 minutes)

### Step 1: Prepare Lambda Functions

```bash
cd ../../lambda

# Orchestrator Actions
cd orchestrator_actions
pip install -r requirements.txt -t .
zip -r ../orchestrator_actions.zip .
cd ..

# Report Actions
cd report_actions
pip install -r requirements.txt -t .
zip -r ../report_actions.zip .
cd ..

# Summarize Actions
cd summarize_actions
pip install -r requirements.txt -t .
zip -r ../summarize_actions.zip .
cd ..

# Code Review Actions
cd code_review_actions
pip install -r requirements.txt -t .
zip -r ../code_review_actions.zip .
cd ..
```

### Step 2: Deploy Multi-Agent System

```bash
cd ../terraform

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region        = "ap-southeast-1"
project_name      = "chatbot-multi-agent"
environment       = "dev"
knowledge_base_id = "$KB_ID"
alert_email       = "your-email@example.com"
EOF

# Deploy
terraform init
terraform plan
terraform apply -auto-approve

# Save agent IDs
export ORCHESTRATOR_AGENT_ID=$(terraform output -raw orchestrator_agent_id)
export ORCHESTRATOR_ALIAS_ID=$(terraform output -raw orchestrator_alias_id)
export REPORT_AGENT_ID=$(terraform output -raw report_agent_id)

echo "Orchestrator Agent: $ORCHESTRATOR_AGENT_ID"
echo "Orchestrator Alias: $ORCHESTRATOR_ALIAS_ID"
```

### Step 3: Verify Agents

```bash
# Check Orchestrator status
aws bedrock-agent get-agent \
  --agent-id $ORCHESTRATOR_AGENT_ID \
  --region ap-southeast-1

# Check if prepared
aws bedrock-agent get-agent-alias \
  --agent-id $ORCHESTRATOR_AGENT_ID \
  --agent-alias-id $ORCHESTRATOR_ALIAS_ID \
  --region ap-southeast-1
```

---

## 🧪 Phase 3: Testing (15 minutes)

### Test 1: Simple Knowledge Base Query

```python
# test_simple_query.py

import boto3
import json
import os

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

def test_simple_query():
    response = bedrock.invoke_agent(
        agentId=os.environ['ORCHESTRATOR_AGENT_ID'],
        agentAliasId=os.environ['ORCHESTRATOR_ALIAS_ID'],
        sessionId='test-session-1',
        inputText="What are the recent issues in GitLab?"
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("✅ Simple Query Test")
    print("Question: What are the recent issues in GitLab?")
    print(f"Answer: {result}\n")
    return result

if __name__ == "__main__":
    test_simple_query()
```

```bash
# Run test
python3 test_simple_query.py
```

### Test 2: Agent Action

```python
# test_agent_action.py

import boto3
import os

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

def test_create_ticket():
    response = bedrock.invoke_agent(
        agentId=os.environ['ORCHESTRATOR_AGENT_ID'],
        agentAliasId=os.environ['ORCHESTRATOR_ALIAS_ID'],
        sessionId='test-session-2',
        inputText="""
        Create a Backlog ticket with the following details:
        - Project: TEST
        - Title: Login bug fix needed
        - Description: Users report login timeout after 30 seconds
        - Priority: High
        - Type: Bug
        """
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("✅ Agent Action Test")
    print("Request: Create Backlog ticket")
    print(f"Result: {result}\n")
    return result

if __name__ == "__main__":
    test_create_ticket()
```

```bash
python3 test_agent_action.py
```

### Test 3: Multi-Agent Coordination

```python
# test_multi_agent.py

import boto3
import os

bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

def test_multi_agent():
    response = bedrock.invoke_agent(
        agentId=os.environ['ORCHESTRATOR_AGENT_ID'],
        agentAliasId=os.environ['ORCHESTRATOR_ALIAS_ID'],
        sessionId='test-session-3',
        inputText="""
        Please do the following:
        1. Summarize today's discussions in the #engineering Slack channel
        2. If any bugs are mentioned, create Backlog tickets for them
        3. Post a summary back to Slack with ticket links
        """
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("✅ Multi-Agent Coordination Test")
    print("Complex workflow executed")
    print(f"Result: {result}\n")
    return result

if __name__ == "__main__":
    test_multi_agent()
```

```bash
python3 test_multi_agent.py
```

---

## 🎨 Phase 4: Production Ready (30 minutes)

### Step 1: Setup API Gateway

```bash
# Deploy API Gateway
cd terraform/api-gateway
terraform init
terraform apply \
  -var="orchestrator_agent_id=$ORCHESTRATOR_AGENT_ID" \
  -var="orchestrator_alias_id=$ORCHESTRATOR_ALIAS_ID" \
  -auto-approve

# Get API endpoint
export API_ENDPOINT=$(terraform output -raw api_endpoint)
echo "API Endpoint: $API_ENDPOINT"
```

### Step 2: Setup Authentication

```bash
# Create Cognito user pool
aws cognito-idp create-user-pool \
  --pool-name chatbot-users \
  --auto-verified-attributes email \
  --region ap-southeast-1

# Get User Pool ID
export USER_POOL_ID=$(aws cognito-idp list-user-pools \
  --max-results 10 \
  --region ap-southeast-1 \
  --query "UserPools[?Name=='chatbot-users'].Id" \
  --output text)

# Create app client
aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name chatbot-web-client \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --region ap-southeast-1

# Get Client ID
export CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id $USER_POOL_ID \
  --region ap-southeast-1 \
  --query "UserPoolClients[0].ClientId" \
  --output text)

echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
```

### Step 3: Create Test User

```bash
# Create test user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS \
  --region ap-southeast-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --password SecurePass123! \
  --permanent \
  --region ap-southeast-1
```

### Step 4: Test API

```python
# test_api.py

import boto3
import requests
import json

cognito = boto3.client('cognito-idp', region_name='ap-southeast-1')

def get_token(username, password, client_id):
    """Get authentication token"""
    response = cognito.initiate_auth(
        ClientId=client_id,
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password
        }
    )
    return response['AuthenticationResult']['IdToken']

def test_api(api_endpoint, token):
    """Test API endpoint"""
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Simple query
    data1 = {
        'message': 'What are the open issues?',
        'conversation_id': 'test_conv_1'
    }
    
    response1 = requests.post(
        f'{api_endpoint}/chat',
        headers=headers,
        json=data1
    )
    
    print("✅ API Test 1: Simple Query")
    print(f"Status: {response1.status_code}")
    print(f"Response: {response1.json()}\n")
    
    # Test 2: Create ticket
    data2 = {
        'message': 'Create a high priority ticket for the payment bug',
        'conversation_id': 'test_conv_1'
    }
    
    response2 = requests.post(
        f'{api_endpoint}/chat',
        headers=headers,
        json=data2
    )
    
    print("✅ API Test 2: Create Ticket")
    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.json()}\n")

if __name__ == "__main__":
    import os
    
    client_id = os.environ['CLIENT_ID']
    api_endpoint = os.environ['API_ENDPOINT']
    
    # Get token
    token = get_token('test@example.com', 'SecurePass123!', client_id)
    
    # Test API
    test_api(api_endpoint, token)
```

```bash
python3 test_api.py
```

---

## 📊 Monitoring Setup

### CloudWatch Dashboard

```bash
# Create monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ChatbotMultiAgent \
  --dashboard-body file://dashboard.json \
  --region ap-southeast-1
```

```json
// dashboard.json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Bedrock", "InvocationLatency", {"stat": "Average"}],
          [".", "TokenCount", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "Bedrock Agents Performance"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-southeast-1",
        "title": "Lambda Functions"
      }
    }
  ]
}
```

### Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ChatbotHighErrorRate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --region ap-southeast-1
```

---

## 🎯 Example Use Cases

### Use Case 1: Daily Standup Report

```
User: "Create a daily standup report including:
- Yesterday's completed tasks from Backlog
- Today's Slack discussions summary
- Blocked issues from GitLab

Post the report to #standup channel"

Orchestrator:
1. ✅ Queries Knowledge Base for completed tasks
2. ✅ Invokes Summarize Agent for Slack discussions
3. ✅ Invokes Code Review Agent for blocked MRs
4. ✅ Invokes Report Agent to post to Slack
5. ✅ Returns confirmation with report link
```

### Use Case 2: Bug Triage Automation

```
User: "Review all bugs mentioned in #engineering channel today.
For each bug:
- Create a Backlog ticket
- Assign to the appropriate developer
- Post confirmation in thread"

Orchestrator:
1. ✅ Invokes Summarize Agent to extract bugs from Slack
2. ✅ For each bug, invokes Report Agent to create ticket
3. ✅ Uses Knowledge Base to find appropriate assignees
4. ✅ Invokes Report Agent to post confirmations
5. ✅ Returns summary of created tickets
```

### Use Case 3: Code Review Summary

```
User: "Summarize all merge requests from last week,
group by project, and post to #code-review"

Orchestrator:
1. ✅ Invokes Code Review Agent to fetch MRs
2. ✅ Groups and summarizes by project
3. ✅ Invokes Report Agent to format and post
4. ✅ Returns confirmation
```

---

## 💡 Troubleshooting

### Issue 1: Agent Not Responding

```bash
# Check agent status
aws bedrock-agent get-agent \
  --agent-id $ORCHESTRATOR_AGENT_ID \
  --region ap-southeast-1

# Check if alias is ready
aws bedrock-agent get-agent-alias \
  --agent-id $ORCHESTRATOR_AGENT_ID \
  --agent-alias-id $ORCHESTRATOR_ALIAS_ID \
  --region ap-southeast-1

# Re-prepare agent if needed
aws bedrock-agent prepare-agent \
  --agent-id $ORCHESTRATOR_AGENT_ID \
  --region ap-southeast-1
```

### Issue 2: Lambda Timeout

```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name orchestrator-actions \
  --timeout 120 \
  --region ap-southeast-1

# Increase memory
aws lambda update-function-configuration \
  --function-name orchestrator-actions \
  --memory-size 2048 \
  --region ap-southeast-1
```

### Issue 3: Permission Errors

```bash
# Check Lambda execution role
aws iam get-role \
  --role-name chatbot-multi-agent-lambda-execution-role

# Check Bedrock agent role
aws iam get-role \
  --role-name chatbot-multi-agent-bedrock-agent-role

# Update policies if needed
aws iam put-role-policy \
  --role-name ... \
  --policy-name ... \
  --policy-document file://policy.json
```

---

## 📈 Performance Optimization

### 1. Enable Response Caching

```bash
# Create ElastiCache cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id chatbot-cache \
  --engine redis \
  --cache-node-type cache.t4g.small \
  --num-cache-nodes 1 \
  --region ap-southeast-1

# Update Lambda environment
aws lambda update-function-configuration \
  --function-name chat-handler \
  --environment "Variables={CACHE_ENDPOINT=your-cache-endpoint}" \
  --region ap-southeast-1
```

### 2. Optimize Knowledge Base

```bash
# Update chunking strategy for better retrieval
aws bedrock-agent update-data-source \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --vector-ingestion-configuration '{
    "chunkingConfiguration": {
      "chunkingStrategy": "FIXED_SIZE",
      "fixedSizeChunkingConfiguration": {
        "maxTokens": 500,
        "overlapPercentage": 20
      }
    }
  }' \
  --region ap-southeast-1
```

### 3. Monitor and Tune

```bash
# View X-Ray traces
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --region ap-southeast-1

# Analyze slow requests
aws xray batch-get-traces \
  --trace-ids [...] \
  --region ap-southeast-1
```

---

## 🎓 Next Steps

1. **Add More Agents**
   - Custom agents for specific workflows
   - Integration with more services

2. **Frontend Development**
   - React/Vue.js web interface
   - Mobile app

3. **Advanced Features**
   - Voice input/output
   - Image understanding
   - Document processing

4. **Production Hardening**
   - Multi-region deployment
   - Advanced security
   - Compliance controls

---

## 📚 Resources

- [Architecture Documentation](./orchestrator-architecture.md)
- [Implementation Guide](./orchestrator-implementation.md)
- [Terraform IaC](./orchestrator-terraform.md)
- [AWS Bedrock Agents Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Example Code Repository](https://github.com/yourcompany/chatbot-multi-agent)

---

## ✅ Deployment Checklist

- [ ] API credentials stored in Secrets Manager
- [ ] Knowledge Base deployed and synced
- [ ] All 4 agents created and prepared
- [ ] Lambda functions deployed
- [ ] API Gateway configured
- [ ] Cognito authentication setup
- [ ] Monitoring dashboard created
- [ ] Alarms configured
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Team trained

**🎉 Congratulations! Your Multi-Agent Orchestrator system is ready for production!**
