# AI Backend System

> **Enterprise-grade AI chatbot backend system with Clean Architecture, AWS Lambda, and real-time WebSocket support**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20Bedrock-orange.svg)](https://aws.amazon.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Contributing](#contributing)

---

## 🎯 Overview

This AI Backend System is a production-ready, scalable solution for building intelligent chatbot applications. Built on **Clean Architecture** principles, it provides a robust foundation for:

- **Real-time AI conversations** via WebSocket with streaming responses
- **Multi-tenant workspaces** with fine-grained RBAC
- **Event-driven data ingestion** from Slack, GitLab, Backlog
- **Tool calling capabilities** for extended AI functionality
- **Polyglot persistence** using PostgreSQL + DynamoDB
- **Serverless deployment** on AWS Lambda

### Key Design Principles

✅ **Clean Architecture** - Domain-centric, testable, maintainable
✅ **Polyglot Persistence** - Right database for the right data
✅ **Event-Driven** - Decoupled, scalable ingestion pipeline
✅ **Security First** - JWT authentication, RBAC, workspace isolation
✅ **Cloud Native** - Serverless, auto-scaling, cost-optimized

---

## ✨ Features

### Core Capabilities

- **Real-time Chat** - WebSocket-based streaming AI responses powered by AWS Bedrock
- **User Management** - Complete user lifecycle with authentication and authorization
- **Workspace Isolation** - Multi-tenant architecture with workspace-scoped data access
- **Chatbot Configuration** - Customizable AI assistants with model parameters and system prompts
- **Conversation History** - Persistent chat sessions stored in DynamoDB
- **Feedback System** - User ratings and feedback collection for AI responses
- **Tool Calling** - Extensible tool registry for AI-driven actions
- **Data Ingestion** - Scheduled ingestion from external platforms (Slack, GitLab, Backlog)

### Technical Features

- **Async/Await** - Fully asynchronous Python with asyncio
- **Type Safety** - Comprehensive type hints and Pydantic models
- **Error Handling** - Structured exception hierarchy with proper HTTP status codes
- **Logging** - JSON-structured logging for CloudWatch integration
- **Health Checks** - Ready/liveness probes for orchestration
- **CORS Support** - Configurable cross-origin resource sharing
- **Rate Limiting** - Protect APIs from abuse
- **API Versioning** - Support for multiple API versions

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Admin UI (Dashboard)                    │
│                      Mobile/Web Clients                       │
└──────────────────────┬─────────────────┬────────────────────┘
                       │ REST (JWT)      │ WebSocket
                       │                 │
┌──────────────────────▼─────────────────▼────────────────────┐
│                    API Gateway (HTTP + WS)                   │
│              EventBridge Scheduler (Ingestion)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    AWS Lambda Functions                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   REST   │  │WebSocket │  │Ingestion │  │Embedding │   │
│  │   API    │  │  Handler │  │   Jobs   │  │  Worker  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└───────┬──────────────┬─────────────┬──────────────┬────────┘
        │              │             │              │
        ▼              ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐  ┌──────────────┐
│ PostgreSQL   │ │ DynamoDB │ │   S3    │  │AWS Bedrock   │
│    (RDS)     │ │          │ │ Buckets │  │(Claude 3)    │
│              │ │          │ │         │  │              │
│ Users, RBAC  │ │Messages  │ │Documents│  │AI Inference  │
│ Workspaces   │ │Feedback  │ │Embeddings│  │              │
│ Chatbots     │ │History   │ │         │  │              │
└──────────────┘ └──────────┘ └─────────┘  └──────────────┘
```

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│          (FastAPI Controllers, WebSocket Handlers)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     Application Layer                        │
│        (Services, Use Cases, Tool Registry)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                       Domain Layer                           │
│        (Entities, Value Objects, Domain Logic)               │
└──────────────────────▲──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                    Infrastructure Layer                      │
│    (Database Clients, AWS Services, External APIs)          │
└─────────────────────────────────────────────────────────────┘
```

### Database Strategy

| Database | Purpose | Data Types |
|----------|---------|------------|
| **PostgreSQL (RDS)** | Relational data with ACID guarantees | Users, Roles, Workspaces, Chatbots, Sessions, Tools |
| **DynamoDB** | High-throughput, scalable NoSQL | Conversation messages, Feedback logs, Embedding references, Ingestion jobs |

**Rationale**: Polyglot persistence allows us to use the best database for each data type:
- PostgreSQL for complex joins and transactional integrity
- DynamoDB for high-volume chat messages and analytics

---

## 🛠️ Technology Stack

### Core Framework
- **FastAPI** 0.104.1 - Modern, fast web framework
- **Python** 3.12 - Latest Python with performance improvements
- **Pydantic** 2.5.0 - Data validation and settings management
- **Uvicorn** - ASGI server with WebSocket support

### Databases
- **PostgreSQL** (via SQLAlchemy + asyncpg) - Relational data
- **DynamoDB** (via boto3) - NoSQL document store

### AWS Services
- **Lambda** - Serverless compute
- **API Gateway** - REST + WebSocket APIs
- **Bedrock** - Claude 3 AI models
- **S3** - Document and embedding storage
- **EventBridge** - Event-driven scheduling
- **RDS** - Managed PostgreSQL
- **OpenSearch** - Vector search (optional)

### Authentication & Security
- **JWT** - Token-based authentication
- **Bcrypt** - Password hashing
- **RBAC** - Role-based access control

### Development Tools
- **pytest** - Testing framework
- **black** - Code formatting
- **mypy** - Static type checking
- **pre-commit** - Git hooks for quality checks

---

## 📁 Project Structure

```
chat-bot/
├── src/
│   ├── api/                          # Presentation Layer
│   │   ├── routers/
│   │   │   ├── auth_routes.py
│   │   │   ├── user_routes.py
│   │   │   ├── role_routes.py
│   │   │   ├── workspace_routes.py
│   │   │   ├── chatbot_routes.py
│   │   │   ├── conversation_routes.py
│   │   │   └── feedback_routes.py
│   │   ├── controllers/              # REST API endpoints
│   │   │   ├── auth_controller.py    # Authentication endpoints
│   │   │   ├── user_controller.py    # User management
│   │   │   ├── workspace_controller.py
│   │   │   ├── chatbot_controller.py
│   │   │   ├── conversation_controller.py
│   │   │   └── feedback_controller.py
│   │   ├── websocket/                # WebSocket handlers
│   │   │   ├── chat_ws_handler.py    # Real-time chat
│   │   │   └── connections_manager.py
│   │   └── middlewares/              # Route-level middleware
│   │       ├── jwt_middleware.py     # JWT validation
│   │       └── rbac_middleware.py    # Permission checks
│   │
│   ├── application/                  # Application Layer
│   │   ├── services/                 # Business logic services
│   │   │   ├── auth_service.py       # Authentication logic
│   │   │   ├── user_service.py
│   │   │   ├── workspace_service.py
│   │   │   ├── chatbot_service.py
│   │   │   ├── conversation_service.py
│   │   │   └── feedback_service.py
│   │   └── tool_registry/            # AI tool system
│   │       ├── tool_manager.py       # Tool registration
│   │       └── web_search_tool.py    # Example tool
│   │
│   ├── usecases/              
│   │   ├── auth_use_cases.py
│   │   ├── chatbot_use_cases.py
│   │   ├── conversation_use_cases.py
│   │   ├── user_use_cases.py
│   │
│   ├── domain/                       # Domain Layer
│   │   ├── entities/                 # Business entities
│   │   │   ├── user.py               # User domain model
│   │   │   ├── role.py               # Role with permissions
│   │   │   ├── workspace.py          # Workspace model
│   │   │   ├── chatbot.py            # Chatbot configuration
│   │   │   ├── message.py            # Chat message
│   │   │   └── feedback.py           # User feedback
│   │   └── value_objects/            # Immutable value objects
│   │   │   ├── email.py              # Email with validation
│   │   │   └── uuid_vo.py            # Type-safe UUIDs
│   │   └── events/  
│   ├── shared/
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── role_repository.py
│   │   │   ├── workspace_repository.py
│   │   │   ├── chatbot_repository.py
│   │   │   ├── conversation_repository.py
│   │   │   └── feedback_repository.py
│   │
│   ├── infrastructure/               # Infrastructure Layer
│   │   ├── dynamodb/                 # DynamoDB clients
│   │   │   ├── dynamo_client.py      # Generic DynamoDB client
│   │   │   ├── conversation_repo.py  # Message repository
│   │   │   └── feedback_repo.py      # Feedback repository
│   │   ├── postgresql/               # PostgreSQL clients
│   │   │   ├── pg_client.py          # SQLAlchemy setup
│   │   │   ├── user_repo.py          # User repository
│   │   │   ├── workspace_repo.py
│   │   │   └── chatbot_repo.py
│   │   ├── bedrock/                  # AWS Bedrock
│   │   │   └── bedrock_client.py     # AI model client
│   │   ├── tools/                    # External tool clients
│   │   │   ├── web_search_client.py
│   │   │   └── backlog_client.py
│   │   └── auth/                     # Auth infrastructure
│   │       └── jwt_handler.py        # JWT operations
│   │
│   ├── core/                         # Core utilities
│   │   ├── config.py                 # Configuration management
│   │   ├── logger.py                 # Structured logging
│   │   ├── errors.py                 # Exception hierarchy
│   │   ├── di.py                     # Dependency injection
│   │   └── middlewares/              # App-level middleware
│   │       ├── request_id.py         # Request tracking
│   │       └── error_handler.py      # Global error handling
│   │
│   ├── schemas/                      # Pydantic DTOs
│   │   ├── auth_schema.py            # Auth request/response
│   │   ├── user_schema.py            # User DTOs
│   │   ├── chatbot_schema.py         # Chatbot DTOs
│   │   └── conversation_schema.py    # Message DTOs
│   │
│   ├── helpers/                      # Helper utilities
│   │   ├── constants.py              # Application constants
│   │   ├── time_utils.py             # Date/time helpers
│   │   ├── prompt_helper.py          # Prompt templates
│   │   └── chunk_utils.py            # Text chunking
│   │
│   ├── ingestion/                    # Data ingestion system
│   │   ├── providers/                # External data sources
│   │   │   ├── slack_provider.py     # Slack ingestion
│   │   │   ├── gitlab_provider.py    # GitLab ingestion
│   │   │   └── backlog_provider.py   # Backlog ingestion
│   │   ├── orchestrator.py           # Ingestion coordinator
│   │   └── embedding_worker.py       # Vector embedding
│   │
│   ├── lambda_handlers/              # Lambda entry points
│   │   ├── api_handler.py            # REST API handler
│   │   ├── ws_handler.py             # WebSocket handler
│   │   ├── ingest_orchestrator_handler.py
│   │   └── embed_worker_handler.py
│   │
│   └── main.py                       # FastAPI app initialization
│
├── docker/
│   └── Dockerfile                    # Lambda container image
│
├── infra/                            # Infrastructure as Code
│   └── terraform/                    # Terraform modules
│       ├── modules/
│       │   ├── lambda/
│       │   ├── api_gateway/
│       │   ├── dynamodb/
│       │   ├── rds/
│       │   └── vpc/
│       └── main.tf
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── e2e/                          # End-to-end tests
│
├── .env.example                      # Environment template
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project metadata
└── README.md                         # This file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 14+**
- **Docker** (for local DynamoDB)
- **AWS Account** (for production deployment)
- **AWS CLI** configured with credentials

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/chat-bot.git
cd chat-bot
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

#### 5. Start Local Services

**PostgreSQL** (using Docker):
```bash
docker run --name postgres \
  -e POSTGRES_DB=ai_backend \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:14
```

**DynamoDB Local** (using Docker):
```bash
docker run --name dynamodb-local \
  -p 8000:8000 \
  -d amazon/dynamodb-local
```

#### 6. Initialize Database

```bash
# Run migrations (if using Alembic)
alembic upgrade head

# Or create tables programmatically
python -c "
from src.infrastructure.postgresql.pg_client import get_postgresql_client
import asyncio

async def init():
    client = get_postgresql_client()
    await client.create_tables()

asyncio.run(init())
"
```

#### 7. Create DynamoDB Tables

```bash
# Use AWS CLI or Terraform to create tables
aws dynamodb create-table \
  --table-name Conversations \
  --attribute-definitions \
    AttributeName=convId,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=convId,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

#### 8. Run the Application

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or use the main script
python src/main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed through environment variables. See [`.env.example`](.env.example) for the complete list.

#### Critical Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name (development/staging/production) | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | *Required* |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_DB` | Database name | `ai_backend` |
| `BEDROCK_MODEL_ID` | AWS Bedrock model | `anthropic.claude-3-sonnet...` |
| `AWS_REGION` | AWS region | `us-east-1` |

#### AWS Credentials

Configure AWS credentials using one of:
- **Environment variables**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **AWS CLI profile**: `aws configure`
- **IAM role** (for Lambda deployment)

---

## 💻 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/

# Check types with mypy
mypy src/

# Lint with flake8
flake8 src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding a New API Endpoint

1. **Define Pydantic schemas** in `src/schemas/`
2. **Create service** in `src/application/services/`
3. **Add controller** in `src/api/controllers/`
4. **Register router** in `src/main.py`
5. **Write tests** in `tests/`

Example:
```python
# src/api/controllers/example_controller.py
from fastapi import APIRouter, Depends
from src.schemas.example_schema import ExampleRequest, ExampleResponse

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def create_example(request: ExampleRequest):
    # Implementation
    pass
```

---

## 🚢 Deployment

### AWS Lambda Deployment

#### 1. Build Docker Image

```bash
cd docker
docker build -t ai-backend-api:latest .
```

#### 2. Push to ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag ai-backend-api:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-backend-api:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-backend-api:latest
```

#### 3. Deploy with Terraform

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file=environments/prod/terraform.tfvars

# Apply changes
terraform apply -var-file=environments/prod/terraform.tfvars
```

### Environment-Specific Deployments

```bash
# Development
terraform apply -var-file=environments/dev/terraform.tfvars

# Staging
terraform apply -var-file=environments/staging/terraform.tfvars

# Production
terraform apply -var-file=environments/prod/terraform.tfvars
```

---

## 📚 API Documentation

### Authentication

#### POST `/api/v1/auth/login`

Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Users

#### GET `/api/v1/users/me`

Get current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true
}
```

### WebSocket

#### Connect: `wss://<api-gateway>/ws?token=<jwt_token>`

Establish WebSocket connection for real-time chat.

**Message Format:**
```json
{
  "type": "chat",
  "chatbot_id": "uuid",
  "content": "Hello, how can you help me?"
}
```

**Response Format:**
```json
{
  "type": "assistant",
  "content": "I can help you with...",
  "message_id": "uuid",
  "status": "completed"
}
```

For complete API documentation, visit `/docs` when running the application.

---

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests (isolated)
│   ├── test_user_service.py
│   ├── test_jwt_handler.py
│   └── test_entities.py
├── integration/          # Integration tests (with DB)
│   ├── test_user_repository.py
│   └── test_bedrock_client.py
└── e2e/                  # End-to-end tests
    └── test_chat_flow.py
```

### Testing Best Practices

- **Mock external services** (AWS, databases) in unit tests
- **Use fixtures** for common setup
- **Test edge cases** and error handling
- **Maintain >80% coverage** for critical paths

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Standards

- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Write **docstrings** for public APIs
- Add **tests** for new features
- Update **documentation** as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **AWS Bedrock** - AI model infrastructure
- **Anthropic Claude** - Advanced language models
- **Clean Architecture** - Robert C. Martin

---

## 📞 Support

For issues and questions:
- **GitHub Issues**: [Create an issue](https://github.com/your-org/chat-bot/issues)
- **Documentation**: [Wiki](https://github.com/your-org/chat-bot/wiki)
- **Email**: support@yourcompany.com

---

**Built with ❤️ for scalable AI applications**
