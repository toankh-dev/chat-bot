# Terraform Infrastructure - Multi-Agent Orchestrator System

## Directory Structure

```
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── bedrock_agents.tf
├── lambda_functions.tf
├── api_gateway.tf
└── modules/
    ├── knowledge-base/
    ├── bedrock-agent/
    └── lambda-action-group/
```

## main.tf

```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "chatbot-terraform-state"
    key            = "multi-agent/terraform.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ChatbotMultiAgent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
```

---

## bedrock_agents.tf

```hcl
# ============================================
# IAM Role for Bedrock Agents
# ============================================

resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-bedrock-agent-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:agent/*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name = "BedrockAgentPolicy"
  role = aws_iam_role.bedrock_agent_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:*Agent*"
      }
    ]
  })
}

# ============================================
# Knowledge Base (from previous setup)
# ============================================

# Reference existing Knowledge Base
data "aws_bedrockagent_knowledge_base" "main" {
  knowledge_base_id = var.knowledge_base_id
}

# ============================================
# Orchestrator Agent
# ============================================

resource "aws_bedrockagent_agent" "orchestrator" {
  agent_name              = "${var.project_name}-orchestrator"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model        = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  idle_session_ttl_in_seconds = 600
  
  description = "Main orchestrator that coordinates specialized agents"
  
  instruction = <<-EOT
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
EOT
}

# Associate Knowledge Base with Orchestrator
resource "aws_bedrockagent_agent_knowledge_base_association" "orchestrator_kb" {
  agent_id             = aws_bedrockagent_agent.orchestrator.agent_id
  agent_version        = "DRAFT"
  knowledge_base_id    = data.aws_bedrockagent_knowledge_base.main.knowledge_base_id
  description          = "Historical data from GitLab, Slack, and Backlog"
  knowledge_base_state = "ENABLED"
}

# Orchestrator Action Group
resource "aws_bedrockagent_agent_action_group" "orchestrator_actions" {
  agent_id      = aws_bedrockagent_agent.orchestrator.agent_id
  agent_version = "DRAFT"
  
  action_group_name = "SubAgentInvocation"
  description       = "Invoke specialized sub-agents"
  
  action_group_executor {
    lambda = aws_lambda_function.orchestrator_actions.arn
  }
  
  api_schema {
    payload = jsonencode({
      openapi = "3.0.0"
      info = {
        title   = "Sub-Agent Invocation API"
        version = "1.0.0"
      }
      paths = {
        "/invoke-report-agent" = {
          post = {
            summary     = "Invoke Report Agent"
            operationId = "invokeReportAgent"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      action = {
                        type        = "string"
                        description = "Action to perform"
                      }
                      parameters = {
                        type        = "object"
                        description = "Action parameters"
                      }
                    }
                    required = ["action", "parameters"]
                  }
                }
              }
            }
            responses = {
              "200" = {
                description = "Success"
              }
            }
          }
        }
        "/invoke-summarize-agent" = {
          post = {
            summary     = "Invoke Summarize Agent"
            operationId = "invokeSummarizeAgent"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      action     = { type = "string" }
                      parameters = { type = "object" }
                    }
                    required = ["action", "parameters"]
                  }
                }
              }
            }
            responses = {
              "200" = { description = "Success" }
            }
          }
        }
        "/invoke-code-review-agent" = {
          post = {
            summary     = "Invoke Code Review Agent"
            operationId = "invokeCodeReviewAgent"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      action     = { type = "string" }
                      parameters = { type = "object" }
                    }
                    required = ["action", "parameters"]
                  }
                }
              }
            }
            responses = {
              "200" = { description = "Success" }
            }
          }
        }
      }
    })
  }
  
  depends_on = [aws_lambda_function.orchestrator_actions]
}

# Prepare Orchestrator Agent
resource "null_resource" "prepare_orchestrator" {
  triggers = {
    agent_id = aws_bedrockagent_agent.orchestrator.agent_id
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      aws bedrock-agent prepare-agent \
        --agent-id ${aws_bedrockagent_agent.orchestrator.agent_id} \
        --region ${var.aws_region}
    EOT
  }
  
  depends_on = [
    aws_bedrockagent_agent_action_group.orchestrator_actions,
    aws_bedrockagent_agent_knowledge_base_association.orchestrator_kb
  ]
}

# Create Orchestrator Alias
resource "aws_bedrockagent_agent_alias" "orchestrator_prod" {
  agent_id   = aws_bedrockagent_agent.orchestrator.agent_id
  alias_name = "production"
  description = "Production alias for Orchestrator"
  
  depends_on = [null_resource.prepare_orchestrator]
}

# ============================================
# Report Agent
# ============================================

resource "aws_bedrockagent_agent" "report" {
  agent_name              = "${var.project_name}-report-agent"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model        = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  idle_session_ttl_in_seconds = 600
  
  description = "Creates reports and tickets in Backlog/Slack"
  
  instruction = <<-EOT
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
EOT
}

resource "aws_bedrockagent_agent_action_group" "report_actions" {
  agent_id      = aws_bedrockagent_agent.report.agent_id
  agent_version = "DRAFT"
  
  action_group_name = "ReportActions"
  description       = "Actions for creating and managing reports"
  
  action_group_executor {
    lambda = aws_lambda_function.report_actions.arn
  }
  
  api_schema {
    payload = jsonencode({
      openapi = "3.0.0"
      info = {
        title   = "Report Agent API"
        version = "1.0.0"
      }
      paths = {
        "/create-backlog-ticket" = {
          post = {
            summary     = "Create Backlog ticket"
            operationId = "createBacklogTicket"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      project_key = {
                        type        = "string"
                        description = "Project key"
                      }
                      summary = {
                        type        = "string"
                        description = "Issue title"
                      }
                      description = {
                        type        = "string"
                        description = "Issue description"
                      }
                      issue_type = {
                        type        = "string"
                        description = "Bug, Task, Feature"
                      }
                      priority = {
                        type        = "string"
                        description = "High, Normal, Low"
                      }
                      assignee = {
                        type        = "string"
                        description = "Assignee username"
                      }
                    }
                    required = ["project_key", "summary", "description"]
                  }
                }
              }
            }
            responses = {
              "200" = { description = "Success" }
            }
          }
        }
        "/post-slack-message" = {
          post = {
            summary     = "Post Slack message"
            operationId = "postSlackMessage"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      channel = {
                        type        = "string"
                        description = "Channel name or ID"
                      }
                      message = {
                        type        = "string"
                        description = "Message text"
                      }
                      thread_ts = {
                        type        = "string"
                        description = "Thread timestamp"
                      }
                    }
                    required = ["channel", "message"]
                  }
                }
              }
            }
            responses = {
              "200" = { description = "Success" }
            }
          }
        }
        "/update-backlog-ticket" = {
          post = {
            summary     = "Update Backlog ticket"
            operationId = "updateBacklogTicket"
            requestBody = {
              required = true
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      issue_key = { type = "string" }
                      status    = { type = "string" }
                      comment   = { type = "string" }
                    }
                    required = ["issue_key"]
                  }
                }
              }
            }
            responses = {
              "200" = { description = "Success" }
            }
          }
        }
      }
    })
  }
  
  depends_on = [aws_lambda_function.report_actions]
}

resource "null_resource" "prepare_report_agent" {
  triggers = {
    agent_id = aws_bedrockagent_agent.report.agent_id
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      aws bedrock-agent prepare-agent \
        --agent-id ${aws_bedrockagent_agent.report.agent_id} \
        --region ${var.aws_region}
    EOT
  }
  
  depends_on = [aws_bedrockagent_agent_action_group.report_actions]
}

resource "aws_bedrockagent_agent_alias" "report_prod" {
  agent_id   = aws_bedrockagent_agent.report.agent_id
  alias_name = "production"
  
  depends_on = [null_resource.prepare_report_agent]
}

# ============================================
# Summarize Agent & Code Review Agent
# (Similar structure to Report Agent)
# ============================================

# ... Similar Terraform resources for other agents ...
```

---

## lambda_functions.tf

```hcl
# ============================================
# Lambda Execution Role
# ============================================

resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom" {
  name = "LambdaCustomPolicy"
  role = aws_iam_role.lambda_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:/chatbot/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeAgent"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.conversations.arn
      }
    ]
  })
}

# ============================================
# Lambda Functions
# ============================================

# Orchestrator Actions Lambda
data "archive_file" "orchestrator_actions" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/orchestrator_actions"
  output_path = "${path.module}/lambda/orchestrator_actions.zip"
}

resource "aws_lambda_function" "orchestrator_actions" {
  filename         = data.archive_file.orchestrator_actions.output_path
  function_name    = "${var.project_name}-orchestrator-actions"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.orchestrator_actions.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 1024
  
  environment {
    variables = {
      REPORT_AGENT_ID      = aws_bedrockagent_agent.report.agent_id
      REPORT_ALIAS_ID      = aws_bedrockagent_agent_alias.report_prod.agent_alias_id
      # Add other agent IDs when created
    }
  }
  
  tracing_config {
    mode = "Active"
  }
}

resource "aws_lambda_permission" "allow_bedrock_orchestrator" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orchestrator_actions.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:agent/*"
}

# Report Actions Lambda
data "archive_file" "report_actions" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/report_actions"
  output_path = "${path.module}/lambda/report_actions.zip"
}

resource "aws_lambda_function" "report_actions" {
  filename         = data.archive_file.report_actions.output_path
  function_name    = "${var.project_name}-report-actions"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.report_actions.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512
  
  tracing_config {
    mode = "Active"
  }
}

resource "aws_lambda_permission" "allow_bedrock_report" {
  statement_id  = "AllowBedrockInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.report_actions.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:agent/*"
}

# Chat Handler Lambda (API Gateway entry point)
data "archive_file" "chat_handler" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/chat_handler"
  output_path = "${path.module}/lambda/chat_handler.zip"
}

resource "aws_lambda_function" "chat_handler" {
  filename         = data.archive_file.chat_handler.output_path
  function_name    = "${var.project_name}-chat-handler"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.chat_handler.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 2048
  
  environment {
    variables = {
      ORCHESTRATOR_AGENT_ID    = aws_bedrockagent_agent.orchestrator.agent_id
      ORCHESTRATOR_ALIAS_ID    = aws_bedrockagent_agent_alias.orchestrator_prod.agent_alias_id
      DYNAMODB_TABLE_NAME      = aws_dynamodb_table.conversations.name
    }
  }
  
  reserved_concurrent_executions = 100
  
  tracing_config {
    mode = "Active"
  }
}
```

---

## outputs.tf

```hcl
output "orchestrator_agent_id" {
  description = "Orchestrator Agent ID"
  value       = aws_bedrockagent_agent.orchestrator.agent_id
}

output "orchestrator_alias_id" {
  description = "Orchestrator Agent Alias ID"
  value       = aws_bedrockagent_agent_alias.orchestrator_prod.agent_alias_id
}

output "report_agent_id" {
  description = "Report Agent ID"
  value       = aws_bedrockagent_agent.report.agent_id
}

output "report_alias_id" {
  description = "Report Agent Alias ID"
  value       = aws_bedrockagent_agent_alias.report_prod.agent_alias_id
}

output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/prod"
}

output "test_command" {
  description = "Test command for the API"
  value       = <<-EOT
    curl -X POST ${aws_apigatewayv2_api.main.api_endpoint}/prod/chat \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"message": "What are the open bugs?", "conversation_id": "test_conv_1"}'
  EOT
}
```

---

## variables.tf

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "chatbot-multi-agent"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "knowledge_base_id" {
  description = "Existing Knowledge Base ID"
  type        = string
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
}
```

---

## Deployment Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan \
  -var="environment=dev" \
  -var="knowledge_base_id=YOUR_KB_ID" \
  -var="alert_email=your-email@example.com"

# Apply deployment
terraform apply \
  -var="environment=dev" \
  -var="knowledge_base_id=YOUR_KB_ID" \
  -var="alert_email=your-email@example.com" \
  -auto-approve

# Get outputs
terraform output

# Destroy resources (cleanup)
terraform destroy \
  -var="environment=dev" \
  -var="knowledge_base_id=YOUR_KB_ID" \
  -var="alert_email=your-email@example.com" \
  -auto-approve
```

---

## Cost Estimate for Multi-Agent System

| Component | Monthly Cost (Prod) |
|-----------|---------------------|
| **Bedrock Agents (4 agents)** | ~$200-400 |
| Orchestrator Agent | $60-120 |
| Report Agent | $50-100 |
| Summarize Agent | $50-100 |
| Code Review Agent | $40-80 |
| **Lambda Functions** | ~$10-30 |
| **Knowledge Base** | ~$50-100 |
| **OpenSearch Serverless** | ~$350-700 |
| **Other Services** | ~$100-150 |
| **TOTAL** | **~$710-1,380/month** |

**Note:** Multi-agent system adds $100-300/month compared to single-agent approach, but provides much better modularity and capabilities.
