# Orchestrator & Multi-Agent Implementation Guide

## 📋 Table of Contents

1. [Setup Prerequisites](#setup-prerequisites)
2. [Knowledge Base Setup](#knowledge-base-setup)
3. [Orchestrator Agent Creation](#orchestrator-agent-creation)
4. [Specialized Agents Implementation](#specialized-agents-implementation)
5. [Lambda Action Groups](#lambda-action-groups)
6. [API Integration](#api-integration)
7. [Testing & Debugging](#testing--debugging)

---

## 🛠️ Setup Prerequisites

### Required IAM Roles

```bash
# 1. Bedrock Agent Execution Role
cat > bedrock-agent-role-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name BedrockAgentExecutionRole \
  --assume-role-policy-document file://bedrock-agent-role-trust-policy.json

# 2. Attach permissions
cat > bedrock-agent-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*Agent*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name BedrockAgentExecutionRole \
  --policy-name BedrockAgentPolicy \
  --policy-document file://bedrock-agent-policy.json
```

---

## 📚 Knowledge Base Setup

### 1. Create Knowledge Base (Already done from previous docs)

```python
# This should already be set up from the previous architecture
# We'll reference it in the Orchestrator Agent

KB_ID = "your-knowledge-base-id"
```

---

## 🧠 Orchestrator Agent Creation

### 1. Create Orchestrator Agent

```python
# create_orchestrator_agent.py

import boto3
import json

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

def create_orchestrator_agent():
    """Create the main Orchestrator Agent"""
    
    # Agent instruction
    instruction = """
You are an intelligent orchestrator agent that coordinates multiple specialized agents to help users with project management tasks.

You have access to the following resources:

1. **Knowledge Base**: Contains historical data from GitLab, Slack, and Backlog
   - Use this to answer questions about past issues, discussions, and code changes
   - Search for relevant context before taking actions

2. **Report Agent**: Creates and manages reports
   - Can create Backlog tickets
   - Can post messages to Slack
   - Can update existing tickets

3. **Summarize Agent**: Analyzes Slack conversations
   - Can fetch and summarize Slack messages
   - Can extract action items and decisions
   - Can identify discussion topics

4. **Code Review Agent**: Reviews GitLab code
   - Can fetch merge requests and commits
   - Can analyze code changes
   - Can check coding standards

**Your Responsibilities:**

1. **Analyze** user questions to understand their intent
2. **Plan** the execution strategy:
   - For simple queries: Use Knowledge Base directly
   - For actions: Use appropriate agent(s)
   - For complex tasks: Coordinate multiple agents sequentially or in parallel
3. **Execute** the plan by invoking agents with proper context
4. **Synthesize** results into a clear, helpful response

**Decision Framework:**

- If user asks "What/Where/Show/Find" → Query Knowledge Base
- If user says "Create/Update/Post/Send" → Use Report Agent
- If user wants "Summarize/Analyze" Slack → Use Summarize Agent
- If user wants code review → Use Code Review Agent
- If task requires multiple steps → Execute sequentially, passing context between steps
- If task has independent parts → Execute in parallel for efficiency

**Important Guidelines:**

- Always check Knowledge Base first for context
- Provide citations/sources when referencing data
- Ask for clarification if the request is ambiguous
- Explain your reasoning when coordinating multiple agents
- Handle errors gracefully and provide helpful alternatives
"""

    response = bedrock_agent.create_agent(
        agentName='OrchestratorAgent',
        description='Main orchestrator that coordinates specialized agents',
        instruction=instruction,
        agentResourceRoleArn='arn:aws:iam::ACCOUNT_ID:role/BedrockAgentExecutionRole',
        foundationModel='anthropic.claude-3-5-sonnet-20241022-v2:0',
        idleSessionTTLInSeconds=600
    )
    
    agent_id = response['agent']['agentId']
    print(f"Orchestrator Agent created: {agent_id}")
    
    return agent_id

def associate_knowledge_base(agent_id, kb_id):
    """Associate Knowledge Base with Orchestrator"""
    
    response = bedrock_agent.associate_agent_knowledge_base(
        agentId=agent_id,
        agentVersion='DRAFT',
        knowledgeBaseId=kb_id,
        description='Historical data from GitLab, Slack, and Backlog',
        knowledgeBaseState='ENABLED'
    )
    
    print(f"Knowledge Base {kb_id} associated with agent {agent_id}")

def create_agent_action_group(agent_id, action_group_config):
    """Create action group for invoking sub-agents"""
    
    response = bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='SubAgentInvocation',
        description='Invoke specialized sub-agents',
        actionGroupExecutor={
            'lambda': action_group_config['lambda_arn']
        },
        apiSchema={
            'payload': json.dumps({
                "openapi": "3.0.0",
                "info": {
                    "title": "Sub-Agent Invocation API",
                    "version": "1.0.0"
                },
                "paths": {
                    "/invoke-report-agent": {
                        "post": {
                            "summary": "Invoke Report Agent to create tickets or post messages",
                            "operationId": "invokeReportAgent",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "action": {
                                                    "type": "string",
                                                    "description": "Action to perform: create_backlog_ticket, post_slack_message"
                                                },
                                                "parameters": {
                                                    "type": "object",
                                                    "description": "Parameters for the action"
                                                }
                                            },
                                            "required": ["action", "parameters"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/invoke-summarize-agent": {
                        "post": {
                            "summary": "Invoke Summarize Agent to analyze Slack conversations",
                            "operationId": "invokeSummarizeAgent",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "action": {
                                                    "type": "string",
                                                    "description": "Action: get_messages, summarize, extract_action_items"
                                                },
                                                "parameters": {
                                                    "type": "object"
                                                }
                                            },
                                            "required": ["action", "parameters"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response"
                                }
                            }
                        }
                    },
                    "/invoke-code-review-agent": {
                        "post": {
                            "summary": "Invoke Code Review Agent to analyze GitLab code",
                            "operationId": "invokeCodeReviewAgent",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "action": {
                                                    "type": "string",
                                                    "description": "Action: get_merge_requests, analyze_code"
                                                },
                                                "parameters": {
                                                    "type": "object"
                                                }
                                            },
                                            "required": ["action", "parameters"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Successful response"
                                }
                            }
                        }
                    }
                }
            })
        }
    )
    
    print(f"Action group created for agent {agent_id}")

def prepare_agent(agent_id):
    """Prepare agent for invocation"""
    
    response = bedrock_agent.prepare_agent(
        agentId=agent_id
    )
    
    print(f"Agent {agent_id} prepared")
    return response

def create_agent_alias(agent_id):
    """Create agent alias for production use"""
    
    response = bedrock_agent.create_agent_alias(
        agentId=agent_id,
        agentAliasName='production',
        description='Production alias for Orchestrator Agent'
    )
    
    alias_id = response['agentAlias']['agentAliasId']
    print(f"Agent alias created: {alias_id}")
    
    return alias_id

# Main execution
if __name__ == "__main__":
    # Step 1: Create agent
    agent_id = create_orchestrator_agent()
    
    # Step 2: Associate Knowledge Base
    kb_id = "YOUR_KB_ID"  # From previous setup
    associate_knowledge_base(agent_id, kb_id)
    
    # Step 3: Create action group (after Lambda is deployed)
    # Uncomment after creating the Lambda function
    # action_group_config = {
    #     'lambda_arn': 'arn:aws:lambda:...:function:OrchestratorActionHandler'
    # }
    # create_agent_action_group(agent_id, action_group_config)
    
    # Step 4: Prepare agent
    prepare_agent(agent_id)
    
    # Step 5: Create alias
    alias_id = create_agent_alias(agent_id)
    
    # Save configuration
    config = {
        'agent_id': agent_id,
        'alias_id': alias_id,
        'kb_id': kb_id
    }
    
    with open('orchestrator_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\nOrchestrator Agent setup complete!")
    print(f"Configuration saved to orchestrator_config.json")
```

---

## 🤖 Specialized Agents Implementation

### 1. Report Agent

```python
# create_report_agent.py

import boto3
import json

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

def create_report_agent():
    """Create Report Agent for Backlog/Slack operations"""
    
    instruction = """
You are a specialized Report Agent that creates and manages reports in Backlog and Slack.

**Your Capabilities:**

1. **Backlog Operations:**
   - Create new issues/tickets with detailed descriptions
   - Update existing issues (status, assignee, comments)
   - Add comments to issues
   - Link related issues

2. **Slack Operations:**
   - Post messages to channels
   - Create formatted reports
   - Send direct messages
   - Update existing messages

**Guidelines:**

- Always validate input parameters before creating tickets
- Use clear, structured format for Backlog issue descriptions
- Format Slack messages for readability (use markdown)
- Provide confirmation with links to created resources
- Handle errors gracefully and provide helpful feedback

**When to Ask for Clarification:**

- If project name is ambiguous
- If required fields are missing (title, description)
- If Slack channel doesn't exist
- If assignee is not found
"""

    response = bedrock_agent.create_agent(
        agentName='ReportAgent',
        description='Creates reports and tickets in Backlog/Slack',
        instruction=instruction,
        agentResourceRoleArn='arn:aws:iam::ACCOUNT_ID:role/BedrockAgentExecutionRole',
        foundationModel='anthropic.claude-3-5-sonnet-20241022-v2:0',
        idleSessionTTLInSeconds=600
    )
    
    agent_id = response['agent']['agentId']
    print(f"Report Agent created: {agent_id}")
    
    return agent_id

def create_report_action_group(agent_id, lambda_arn):
    """Create action group for Report Agent"""
    
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Report Agent API",
            "version": "1.0.0"
        },
        "paths": {
            "/create-backlog-ticket": {
                "post": {
                    "summary": "Create a new Backlog ticket",
                    "operationId": "createBacklogTicket",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "project_key": {
                                            "type": "string",
                                            "description": "Backlog project key"
                                        },
                                        "summary": {
                                            "type": "string",
                                            "description": "Issue title/summary"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Detailed issue description"
                                        },
                                        "issue_type": {
                                            "type": "string",
                                            "description": "Bug, Task, Feature, etc."
                                        },
                                        "priority": {
                                            "type": "string",
                                            "description": "High, Normal, Low"
                                        },
                                        "assignee": {
                                            "type": "string",
                                            "description": "Assignee username (optional)"
                                        }
                                    },
                                    "required": ["project_key", "summary", "description"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ticket created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "issue_key": {"type": "string"},
                                            "issue_url": {"type": "string"},
                                            "issue_id": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/post-slack-message": {
                "post": {
                    "summary": "Post a message to Slack channel",
                    "operationId": "postSlackMessage",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "channel": {
                                            "type": "string",
                                            "description": "Channel name or ID"
                                        },
                                        "message": {
                                            "type": "string",
                                            "description": "Message text (supports markdown)"
                                        },
                                        "thread_ts": {
                                            "type": "string",
                                            "description": "Thread timestamp for replies (optional)"
                                        }
                                    },
                                    "required": ["channel", "message"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Message posted successfully"
                        }
                    }
                }
            },
            "/update-backlog-ticket": {
                "post": {
                    "summary": "Update an existing Backlog ticket",
                    "operationId": "updateBacklogTicket",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "issue_key": {
                                            "type": "string",
                                            "description": "Issue key (e.g., PROJ-123)"
                                        },
                                        "status": {
                                            "type": "string",
                                            "description": "New status"
                                        },
                                        "comment": {
                                            "type": "string",
                                            "description": "Comment to add"
                                        }
                                    },
                                    "required": ["issue_key"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ticket updated successfully"
                        }
                    }
                }
            }
        }
    }
    
    response = bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='ReportActions',
        description='Actions for creating and managing reports',
        actionGroupExecutor={
            'lambda': lambda_arn
        },
        apiSchema={
            'payload': json.dumps(api_schema)
        }
    )
    
    print(f"Action group created for Report Agent")

# Main execution
if __name__ == "__main__":
    agent_id = create_report_agent()
    
    # Note: Lambda must be created first
    lambda_arn = "arn:aws:lambda:ap-southeast-1:ACCOUNT_ID:function:ReportAgentActions"
    create_report_action_group(agent_id, lambda_arn)
    
    # Prepare and create alias
    bedrock_agent.prepare_agent(agentId=agent_id)
    alias_response = bedrock_agent.create_agent_alias(
        agentId=agent_id,
        agentAliasName='production'
    )
    
    config = {
        'agent_id': agent_id,
        'alias_id': alias_response['agentAlias']['agentAliasId']
    }
    
    with open('report_agent_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Report Agent setup complete!")
```

### 2. Summarize Agent

```python
# create_summarize_agent.py

import boto3
import json

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

def create_summarize_agent():
    """Create Summarize Agent for Slack analysis"""
    
    instruction = """
You are a specialized Summarize Agent that analyzes Slack conversations and extracts insights.

**Your Capabilities:**

1. **Message Retrieval:**
   - Fetch messages from specific channels
   - Filter by date range, user, or keywords
   - Retrieve threaded conversations

2. **Analysis:**
   - Summarize discussions with key points
   - Extract action items and decisions
   - Identify discussion topics and themes
   - Track sentiment and tone

3. **Extraction:**
   - Find mentions of bugs, features, blockers
   - Extract deadlines and commitments
   - Identify questions that need answers

**Guidelines:**

- Provide concise summaries with bullet points
- Highlight critical information (bugs, blockers, decisions)
- Preserve important context and nuances
- Quote specific messages when relevant
- Note if discussion is still ongoing

**Output Format:**

For summaries:
- Main topic/context
- Key points (3-5 bullet points)
- Action items (who, what, when)
- Open questions

For extractions:
- Categorized findings
- Relevant quotes/snippets
- Links to original messages
"""

    response = bedrock_agent.create_agent(
        agentName='SummarizeAgent',
        description='Analyzes and summarizes Slack conversations',
        instruction=instruction,
        agentResourceRoleArn='arn:aws:iam::ACCOUNT_ID:role/BedrockAgentExecutionRole',
        foundationModel='anthropic.claude-3-5-sonnet-20241022-v2:0',
        idleSessionTTLInSeconds=600
    )
    
    agent_id = response['agent']['agentId']
    print(f"Summarize Agent created: {agent_id}")
    
    return agent_id

def create_summarize_action_group(agent_id, lambda_arn):
    """Create action group for Summarize Agent"""
    
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Summarize Agent API",
            "version": "1.0.0"
        },
        "paths": {
            "/get-slack-messages": {
                "post": {
                    "summary": "Fetch Slack messages",
                    "operationId": "getSlackMessages",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "channel": {
                                            "type": "string",
                                            "description": "Channel name or ID"
                                        },
                                        "start_date": {
                                            "type": "string",
                                            "description": "Start date (YYYY-MM-DD)"
                                        },
                                        "end_date": {
                                            "type": "string",
                                            "description": "End date (YYYY-MM-DD)"
                                        },
                                        "limit": {
                                            "type": "integer",
                                            "description": "Max messages to return"
                                        }
                                    },
                                    "required": ["channel"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Messages retrieved successfully"
                        }
                    }
                }
            },
            "/summarize-discussion": {
                "post": {
                    "summary": "Summarize a Slack discussion",
                    "operationId": "summarizeDiscussion",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "messages": {
                                            "type": "array",
                                            "description": "Array of message objects",
                                            "items": {"type": "object"}
                                        },
                                        "focus": {
                                            "type": "string",
                                            "description": "What to focus on: bugs, features, decisions, general"
                                        }
                                    },
                                    "required": ["messages"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Summary generated"
                        }
                    }
                }
            },
            "/extract-action-items": {
                "post": {
                    "summary": "Extract action items from discussions",
                    "operationId": "extractActionItems",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "messages": {
                                            "type": "array",
                                            "items": {"type": "object"}
                                        }
                                    },
                                    "required": ["messages"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Action items extracted"
                        }
                    }
                }
            }
        }
    }
    
    response = bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='SummarizeActions',
        description='Actions for analyzing Slack conversations',
        actionGroupExecutor={
            'lambda': lambda_arn
        },
        apiSchema={
            'payload': json.dumps(api_schema)
        }
    )
    
    print(f"Action group created for Summarize Agent")

# Main execution similar to Report Agent
```

### 3. Code Review Agent

```python
# create_code_review_agent.py

import boto3
import json

bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

def create_code_review_agent():
    """Create Code Review Agent for GitLab operations"""
    
    instruction = """
You are a specialized Code Review Agent that analyzes GitLab code changes.

**Your Capabilities:**

1. **Merge Request Analysis:**
   - Fetch MR details and diffs
   - Review code changes
   - Check for common issues

2. **Commit History:**
   - Analyze commit messages
   - Track file changes over time
   - Identify patterns

3. **Code Quality:**
   - Check coding standards adherence
   - Identify potential bugs or issues
   - Suggest improvements

**Review Focus Areas:**

- Code structure and organization
- Error handling
- Security concerns
- Performance implications
- Documentation completeness

**Guidelines:**

- Be constructive and specific in feedback
- Prioritize critical issues over style preferences
- Provide code examples for suggestions
- Reference coding standards when applicable
- Acknowledge good practices
"""

    response = bedrock_agent.create_agent(
        agentName='CodeReviewAgent',
        description='Reviews GitLab code changes',
        instruction=instruction,
        agentResourceRoleArn='arn:aws:iam::ACCOUNT_ID:role/BedrockAgentExecutionRole',
        foundationModel='anthropic.claude-3-5-sonnet-20241022-v2:0',
        idleSessionTTLInSeconds=600
    )
    
    agent_id = response['agent']['agentId']
    print(f"Code Review Agent created: {agent_id}")
    
    return agent_id

# Similar action group creation as above
```

---

## 🔌 Lambda Action Groups

### Orchestrator Action Handler

```python
# lambda_orchestrator_actions.py

import json
import boto3

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

# Sub-agent configurations
AGENTS = {
    'report': {
        'agent_id': 'REPORT_AGENT_ID',
        'alias_id': 'REPORT_ALIAS_ID'
    },
    'summarize': {
        'agent_id': 'SUMMARIZE_AGENT_ID',
        'alias_id': 'SUMMARIZE_ALIAS_ID'
    },
    'code_review': {
        'agent_id': 'CODE_REVIEW_AGENT_ID',
        'alias_id': 'CODE_REVIEW_ALIAS_ID'
    }
}

def invoke_sub_agent(agent_type, action, parameters, session_id):
    """Invoke a specialized sub-agent"""
    
    agent_config = AGENTS.get(agent_type)
    if not agent_config:
        return {'error': f'Unknown agent type: {agent_type}'}
    
    # Construct prompt for sub-agent
    prompt = f"Action: {action}\nParameters: {json.dumps(parameters, indent=2)}"
    
    try:
        response = bedrock_runtime.invoke_agent(
            agentId=agent_config['agent_id'],
            agentAliasId=agent_config['alias_id'],
            sessionId=session_id,
            inputText=prompt
        )
        
        # Collect response
        result = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode('utf-8')
        
        return {'success': True, 'result': result}
        
    except Exception as e:
        return {'error': str(e)}

def lambda_handler(event, context):
    """
    Handle action group invocations from Orchestrator Agent
    
    Event structure from Bedrock Agent:
    {
        "actionGroup": "SubAgentInvocation",
        "apiPath": "/invoke-report-agent",
        "httpMethod": "POST",
        "parameters": [...],
        "requestBody": {...},
        "sessionId": "...",
        "sessionAttributes": {...},
        "promptSessionAttributes": {...}
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    api_path = event.get('apiPath', '')
    request_body = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    session_id = event.get('sessionId', '')
    
    # Parse request body
    action_params = {}
    for param in request_body:
        action_params[param['name']] = param['value']
    
    # Determine which agent to invoke
    if '/invoke-report-agent' in api_path:
        result = invoke_sub_agent(
            'report',
            action_params.get('action'),
            action_params.get('parameters', {}),
            session_id
        )
    
    elif '/invoke-summarize-agent' in api_path:
        result = invoke_sub_agent(
            'summarize',
            action_params.get('action'),
            action_params.get('parameters', {}),
            session_id
        )
    
    elif '/invoke-code-review-agent' in api_path:
        result = invoke_sub_agent(
            'code_review',
            action_params.get('action'),
            action_params.get('parameters', {}),
            session_id
        )
    
    else:
        result = {'error': f'Unknown API path: {api_path}'}
    
    # Format response for Bedrock Agent
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    
    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': api_path,
        'httpMethod': event['httpMethod'],
        'httpStatusCode': 200,
        'responseBody': response_body
    }
    
    return {'response': action_response}
```

### Report Agent Action Handler

```python
# lambda_report_actions.py

import json
import boto3
import requests
from datetime import datetime

secrets = boto3.client('secretsmanager', region_name='ap-southeast-1')

def get_secret(secret_name):
    """Get secret from Secrets Manager"""
    response = secrets.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def create_backlog_ticket(params):
    """Create a Backlog ticket"""
    
    # Get Backlog credentials
    backlog_secret = get_secret('/chatbot/backlog/api-key')
    api_key = backlog_secret['api_key']
    space_url = backlog_secret['space_url']
    
    # Prepare request
    url = f"{space_url}/api/v2/issues"
    data = {
        'apiKey': api_key,
        'projectId': params.get('project_key'),
        'summary': params.get('summary'),
        'description': params.get('description'),
        'issueTypeId': params.get('issue_type', 1),
        'priorityId': params.get('priority', 2)
    }
    
    if params.get('assignee'):
        # Look up assignee ID
        users_url = f"{space_url}/api/v2/users"
        users_response = requests.get(users_url, params={'apiKey': api_key})
        users = users_response.json()
        
        for user in users:
            if user['userId'] == params['assignee']:
                data['assigneeId'] = user['id']
                break
    
    # Create ticket
    response = requests.post(url, data=data)
    
    if response.status_code == 201:
        issue = response.json()
        return {
            'success': True,
            'issue_key': issue['issueKey'],
            'issue_url': f"{space_url}/view/{issue['issueKey']}",
            'issue_id': issue['id']
        }
    else:
        return {
            'success': False,
            'error': response.text
        }

def post_slack_message(params):
    """Post message to Slack"""
    
    # Get Slack credentials
    slack_secret = get_secret('/chatbot/slack/bot-token')
    bot_token = slack_secret['bot_token']
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        'Authorization': f'Bearer {bot_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'channel': params.get('channel'),
        'text': params.get('message'),
        'thread_ts': params.get('thread_ts')
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get('ok'):
        return {
            'success': True,
            'timestamp': result['ts'],
            'channel': result['channel']
        }
    else:
        return {
            'success': False,
            'error': result.get('error', 'Unknown error')
        }

def update_backlog_ticket(params):
    """Update an existing Backlog ticket"""
    
    backlog_secret = get_secret('/chatbot/backlog/api-key')
    api_key = backlog_secret['api_key']
    space_url = backlog_secret['space_url']
    
    issue_key = params.get('issue_key')
    
    # Get issue ID from key
    search_url = f"{space_url}/api/v2/issues"
    search_response = requests.get(search_url, params={
        'apiKey': api_key,
        'keyword': issue_key
    })
    
    issues = search_response.json()
    if not issues:
        return {'success': False, 'error': 'Issue not found'}
    
    issue_id = issues[0]['id']
    
    # Update issue
    update_url = f"{space_url}/api/v2/issues/{issue_id}"
    update_data = {'apiKey': api_key}
    
    if params.get('status'):
        update_data['statusId'] = params['status']
    
    response = requests.patch(update_url, data=update_data)
    
    if response.status_code == 200:
        # Add comment if provided
        if params.get('comment'):
            comment_url = f"{space_url}/api/v2/issues/{issue_id}/comments"
            comment_data = {
                'apiKey': api_key,
                'content': params['comment']
            }
            requests.post(comment_url, data=comment_data)
        
        return {'success': True, 'issue_key': issue_key}
    else:
        return {'success': False, 'error': response.text}

def lambda_handler(event, context):
    """Handle Report Agent actions"""
    
    print(f"Received event: {json.dumps(event)}")
    
    api_path = event.get('apiPath', '')
    request_body = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    
    # Parse parameters
    params = {}
    for param in request_body:
        params[param['name']] = param['value']
    
    # Route to appropriate handler
    if '/create-backlog-ticket' in api_path:
        result = create_backlog_ticket(params)
    
    elif '/post-slack-message' in api_path:
        result = post_slack_message(params)
    
    elif '/update-backlog-ticket' in api_path:
        result = update_backlog_ticket(params)
    
    else:
        result = {'success': False, 'error': f'Unknown action: {api_path}'}
    
    # Format response
    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    
    return {
        'response': {
            'actionGroup': event['actionGroup'],
            'apiPath': api_path,
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': response_body
        }
    }
```

---

## 🚀 Complete Implementation Script

```bash
#!/bin/bash
# deploy_multi_agent_system.sh

set -e

echo "🚀 Deploying Multi-Agent System..."

# Step 1: Deploy Lambda functions
echo "📦 Deploying Lambda functions..."

cd lambda/orchestrator_actions
pip install -r requirements.txt -t .
zip -r ../orchestrator_actions.zip .
cd ..

aws lambda create-function \
  --function-name OrchestratorActions \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/LambdaExecutionRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://orchestrator_actions.zip \
  --timeout 60 \
  --memory-size 1024 \
  --environment Variables="{REPORT_AGENT_ID=...,SUMMARIZE_AGENT_ID=...,CODE_REVIEW_AGENT_ID=...}"

# Similar for other Lambda functions...

# Step 2: Create Bedrock Agents
echo "🤖 Creating Bedrock Agents..."
python3 create_orchestrator_agent.py
python3 create_report_agent.py
python3 create_summarize_agent.py
python3 create_code_review_agent.py

# Step 3: Grant Lambda permissions
echo "🔐 Setting up permissions..."
aws lambda add-permission \
  --function-name OrchestratorActions \
  --statement-id allow-bedrock \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com

echo "✅ Deployment complete!"
```

---

## 🧪 Testing

```python
# test_orchestrator.py

import boto3
import json

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

# Load configuration
with open('orchestrator_config.json', 'r') as f:
    config = json.load(f)

def test_simple_query():
    """Test simple knowledge base query"""
    
    response = bedrock_runtime.invoke_agent(
        agentId=config['agent_id'],
        agentAliasId=config['alias_id'],
        sessionId='test-session-1',
        inputText="What are the open bugs in project X?"
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("Response:", result)

def test_action_execution():
    """Test agent action execution"""
    
    response = bedrock_runtime.invoke_agent(
        agentId=config['agent_id'],
        agentAliasId=config['alias_id'],
        sessionId='test-session-2',
        inputText="Create a Backlog ticket for the login bug with high priority"
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("Response:", result)

def test_multi_agent():
    """Test multi-agent coordination"""
    
    response = bedrock_runtime.invoke_agent(
        agentId=config['agent_id'],
        agentAliasId=config['alias_id'],
        sessionId='test-session-3',
        inputText="Summarize yesterday's Slack discussion and create tickets for any bugs mentioned"
    )
    
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result += chunk['bytes'].decode('utf-8')
    
    print("Response:", result)

if __name__ == "__main__":
    print("Test 1: Simple Query")
    test_simple_query()
    
    print("\nTest 2: Action Execution")
    test_action_execution()
    
    print("\nTest 3: Multi-Agent Coordination")
    test_multi_agent()
```

Bạn có muốn tôi tiếp tục tạo thêm documents về testing, monitoring, hoặc frontend integration không? 🚀
