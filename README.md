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
- **Reliable persistence** using PostgreSQL (RDS)
- **Serverless deployment** on AWS Lambda

### Key Design Principles

✅ **Clean Architecture** - Domain-centric, testable, maintainable
✅ **Reliable Persistence** - ACID-compliant relational storage
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
- **Conversation History** - Persistent chat sessions stored in PostgreSQL
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
│ PostgreSQL   │ │   S3    │ │   S3    │  │AWS Bedrock   │
│    (RDS)     │ │ Buckets │ │ Buckets │  │(Claude 3)    │
│              │ │         │ │         │  │              │
│ Users, RBAC  │ │Documents│ │Embeddings│  │AI Inference  │
│ Workspaces   │ │         │ │         │  │              │
│ Chatbots     │ │         │ │         │  │              │
│ Conversations│ │         │ │         │  │              │
│ Messages     │ │         │ │         │  │              │
│ Feedback     │ │         │ │         │  │              │
└──────────────┘ └─────────┘ └─────────┘  └──────────────┘
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
| **PostgreSQL (RDS)** | Relational data with ACID guarantees | Users, Roles, Workspaces, Chatbots, Sessions, Tools, Conversations, Messages, Feedback, Embeddings, Ingestion jobs |

**Rationale**: Using PostgreSQL provides strong consistency, transactional integrity, and powerful querying for all application data, including conversations and messages.

---

## 🛠️ Technology Stack

### Core Framework
- **FastAPI** 0.104.1 - Modern, fast web framework
- **Python** 3.12 - Latest Python with performance improvements
- **Pydantic** 2.5.0 - Data validation and settings management
- **Uvicorn** - ASGI server with WebSocket support

### Databases
- **PostgreSQL** (via SQLAlchemy + asyncpg) - Relational data

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
│   │   ├── controllers/              # REST API endpoints
│   │   │   ├── ai_controller.py      # Unified AI endpoints (RAG + LLM)
│   │   │   ├── auth_controller.py    # Authentication endpoints
│   │   │   ├── chatbot_controller.py # Chatbot management
│   │   │   ├── conversation_controller.py # Chat conversations
│   │   │   ├── document_controller.py # Document upload/management
│   │   │   └── user_controller.py    # User management
│   │   ├── routers/                  # FastAPI route definitions
│   │   │   ├── ai_routes.py          # AI API routes
│   │   │   ├── auth_routes.py        # Authentication routes
│   │   │   ├── chatbot_routes.py     # Chatbot routes
│   │   │   ├── conversation_routes.py # Conversation routes
│   │   │   ├── document_routes.py    # Document routes
│   │   │   └── user_routes.py        # User routes
│   │   └── middlewares/              # Route-level middleware
│   │       └── jwt_middleware.py     # JWT validation
│   │
│   ├── application/                  # Application Layer
│   │   └── services/                 # Business logic services
│   │       ├── auth_service.py       # Authentication logic
│   │       ├── chatbot_service.py    # Chatbot business logic
│   │       ├── conversation_service.py # Conversation management
│   │       ├── document_upload_service.py # Document processing
│   │       ├── rag_service.py        # RAG workflow logic
│   │       ├── user_service.py       # User management logic
│   │       └── vector_store_service.py # Vector store operations
│   │
│   ├── usecases/                     # Use Case Layer
│   │   ├── auth_use_cases.py         # Authentication use cases
│   │   ├── chatbot_use_cases.py      # Chatbot use cases
│   │   ├── conversation_use_cases.py # Conversation use cases
│   │   ├── document_use_cases.py     # Document use cases
│   │   ├── rag_use_cases.py          # RAG use cases
│   │   └── user_use_cases.py         # User use cases
│   │
│   ├── domain/                       # Domain Layer
│   │   ├── entities/                 # Business entities
│   │   │   ├── chatbot.py            # Chatbot domain model
│   │   │   ├── conversation.py       # Conversation domain model
│   │   │   ├── document.py           # Document domain model
│   │   │   ├── embedding_index.py    # Embedding index model
│   │   │   ├── feedback.py           # User feedback model
│   │   │   ├── ingestion_job.py      # Data ingestion job model
│   │   │   ├── message.py            # Chat message model
│   │   │   ├── role.py               # User role model
│   │   │   ├── user.py               # User domain model
│   │   │   └── workspace.py          # Workspace model
│   │   └── value_objects/            # Immutable value objects
│   │       ├── email.py              # Email with validation
│   │       └── uuid_vo.py            # Type-safe UUIDs
│   │
│   ├── shared/                       # Shared interfaces
│   │   └── interfaces/               # Clean interface organization
│   │       ├── repositories/         # Repository interfaces
│   │       │   ├── base_repository.py # Base repository interface
│   │       │   ├── chatbot_repository.py # Chatbot repository interface
│   │       │   ├── conversation_repository.py # Conversation repository interface
│   │       │   ├── document_repository.py # Document repository interface
│   │       │   ├── embedding_index_repository.py # Embedding repository interface
│   │       │   ├── feedback_repository.py # Feedback repository interface
│   │       │   ├── ingestion_job_repository.py # Ingestion job repository interface
│   │       │   ├── message_repository.py # Message repository interface
│   │       │   ├── role_repository.py # Role repository interface
│   │       │   ├── user_repository.py # User repository interface
│   │       │   └── workspace_repository.py # Workspace repository interface
│   │       ├── services/             # Service interfaces
│   │       │   ├── ai_services/      # AI-related service interfaces
│   │       │   │   ├── embedding_service.py # Embedding service interface
│   │       │   │   ├── knowledge_base_service.py # Knowledge base service interface
│   │       │   │   ├── rag_service.py # RAG service interface
│   │       │   │   └── vector_store_service.py # Vector store service interface
│   │       │   ├── storage/          # Storage service interfaces
│   │       │   │   └── file_storage_service.py # File storage service interface
│   │       │   └── upload/           # Upload service interfaces
│   │       │       └── document_upload_service.py # Document upload service interface
│   │       └── types/                # Type interfaces
│   │
│   ├── infrastructure/               # Infrastructure Layer
│   │   ├── ai_services/              # AI service implementations
│   │   │   ├── factory.py            # AI service factory
│   │   │   ├── providers/            # AI provider implementations
│   │   │   │   ├── base.py           # Base AI provider
│   │   │   │   ├── bedrock.py        # AWS Bedrock provider
│   │   │   │   └── gemini.py         # Google Gemini provider
│   │   │   └── services/             # AI service implementations
│   │   │       ├── embedding.py     # Embedding service implementation
│   │   │       └── knowledge_base.py # Knowledge base service implementation
│   │   ├── auth/                     # Authentication infrastructure
│   │   │   └── jwt_handler.py        # JWT operations
│   │   ├── postgresql/               # PostgreSQL infrastructure
│   │   │   ├── connection/           # Database connection management
│   │   │   │   ├── base.py           # SQLAlchemy base configuration
│   │   │   │   └── database.py       # Database session management
│   │   │   ├── models/               # SQLAlchemy models
│   │   │   │   ├── chatbot_model.py  # Chatbot database model
│   │   │   │   ├── conversation_model.py # Conversation database model
│   │   │   │   ├── document_model.py # Document database model
│   │   │   │   └── user_model.py     # User database model
│   │   │   ├── repositories/         # Repository implementations
│   │   │   │   ├── chatbot_repository.py # Chatbot repository implementation
│   │   │   │   ├── conversation_repository.py # Conversation repository implementation
│   │   │   │   ├── document_repository.py # Document repository implementation
│   │   │   │   ├── embedding_index_repository.py # Embedding repository implementation
│   │   │   │   ├── ingestion_job_repository.py # Ingestion job repository implementation
│   │   │   │   └── user_repository.py # User repository implementation
│   │   │   └── mappers/              # Domain ↔ Model mappers
│   │   │       ├── chatbot_mapper.py # Chatbot entity mapper
│   │   │       ├── conversation_mapper.py # Conversation entity mapper
│   │   │       ├── document_mapper.py # Document entity mapper
│   │   │       ├── message_mapper.py # Message entity mapper
│   │   │       └── user_mapper.py    # User entity mapper
│   │   ├── s3/                       # S3 storage infrastructure
│   │   │   ├── file_storage_service_impl.py # File storage implementation
│   │   │   └── s3_file_storage_service.py # S3 storage service
│   │   └── vector_store/             # Vector store infrastructure
│   │       ├── base.py               # Base vector store
│   │       ├── factory.py            # Vector store factory
│   │       └── providers/            # Vector store providers
│   │           ├── chromadb.py       # ChromaDB provider
│   │           └── s3_vector.py      # S3 vector provider
│   │
│   ├── schemas/                      # Pydantic DTOs
│   │   ├── auth_schema.py            # Auth request/response schemas
│   │   ├── chatbot_schema.py         # Chatbot DTOs
│   │   ├── conversation_schema.py    # Conversation DTOs
│   │   ├── document_schema.py        # Document DTOs
│   │   ├── rag_schema.py             # RAG DTOs
│   │   └── user_schema.py            # User DTOs
│   │
│   ├── core/                         # Core utilities
│   │   ├── config.py                 # Configuration management
│   │   ├── dependencies.py           # Dependency injection
│   │   ├── errors.py                 # Exception hierarchy
│   │   └── logger.py                 # Structured logging
│   │
│   ├── lambda_handlers/              # Lambda entry points
│   │   ├── api_handler.py            # REST API handler
│   │   └── ws_handler.py             # WebSocket handler
│   │
│   ├── helpers/                      # Helper utilities
│   ├── ingestion/                    # Data ingestion system
│   │
│   └── main.py                       # FastAPI app initialization
│
├── alembic/                          # Database migrations
│   ├── versions/                     # Migration files
│   ├── env.py                        # Alembic environment
│   └── script.py.mako               # Migration template
│
├── docker/                           # Docker configuration
│   ├── Dockerfile                    # Application container
│   └── init.sql                      # Database initialization
│
├── terraform/                        # Infrastructure as Code
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   ├── conftest.py                   # Test configuration
│   └── test_*.py                     # Test files
│
├── scripts/                          # Utility scripts
├── docker-compose.yml                # Local development setup
├── Dockerfile.dev                    # Development container
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
- **Docker** (for local PostgreSQL)
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

#### 7. Run the Application

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

## API Documentation

See `/docs` when running the application for full OpenAPI documentation.

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
