# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KASS AI Backend System is an enterprise-grade AI chatbot backend built with Python and FastAPI, implementing Clean Architecture principles. It provides real-time WebSocket AI chat capabilities with RAG (Retrieval-Augmented Generation), multi-tenant workspaces, and external integrations (GitLab, Slack, Backlog).

## Architecture

The codebase follows Clean Architecture with these layers:

```
src/
├── api/                    # Presentation Layer - REST API controllers, WebSocket handlers, JWT middleware
├── application/           # Application Layer - Business logic services
├── usecases/             # Use Case Layer - Specific business use cases orchestrating logic
├── domain/               # Domain Layer - Core business entities, value objects, business rules
├── infrastructure/       # Infrastructure Layer - PostgreSQL, AWS services, AI providers, vector stores
└── shared/               # Shared Interfaces - Repository interfaces, service interfaces, types
```

Key architectural principles:
- Dependency inversion with repository interfaces in `shared/` implemented in `infrastructure/`
- Use cases orchestrate business logic between application and domain layers
- Controllers handle HTTP/WebSocket concerns, delegating to use cases
- Domain entities contain business logic, infrastructure handles technical concerns

## Common Development Commands

### Running the Application
```bash
# Development server with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Docker Compose (recommended - includes PostgreSQL, Redis, ChromaDB)
docker-compose up -d
```

### Database Operations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Seed database with test data
python alembic/seed.py
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_gitlab_service.py -v

# Run tests matching pattern
pytest tests/ -k gitlab -v
```

### Code Quality
```bash
# Format code
black src/

# Lint
flake8 src/ --max-line-length=100 --extend-ignore=E203,W503

# Type check
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Key Technical Details

### Database
- PostgreSQL with SQLAlchemy ORM
- Alembic for migrations (timestamp-based versioning)
- Connection management via `get_postgresql_client()` factory

### AI Models
- Development: Google Gemini API
- Production: AWS Bedrock (Claude)
- Vector stores: ChromaDB (local), S3 (production)

### Authentication
- JWT-based with role-based access control (RBAC)
- Middleware in `src/api/middleware/jwt_middleware.py`
- Session parameter consistency: use `x-session-id` header

### External Integrations
- GitLab: Repository data ingestion, commit analysis, code indexing
- Slack: Message history import
- Backlog: Project data synchronization

### WebSocket Implementation
- Real-time AI streaming responses
- Connection management in `src/api/controllers/ai_controller.py`
- Message queue processing for async operations

## Development Guidelines

### When Adding New Features
1. Start with domain entities in `src/domain/`
2. Create repository interfaces in `src/shared/interfaces/repositories/`
3. Implement repositories in `src/infrastructure/postgresql/repositories/`
4. Create use cases in `src/usecases/`
5. Add controllers in `src/api/controllers/`
6. Register routes in `src/api/routers/`

### Error Handling
- Use domain-specific exceptions in `src/domain/exceptions/`
- Controllers should catch and convert to HTTP responses
- Always include error codes and user-friendly messages

### Testing Requirements
- Unit tests for domain logic and use cases
- Integration tests for repository implementations
- Mock external services (AI providers, AWS) in tests
- Use pytest fixtures for common test data

### Environment Configuration
- Copy `.env.example` to `.env` for local development
- Use local file storage and Google Gemini for development
- AWS services (Bedrock, S3) for production only

## Current Development Focus

The `feature/refator` branch is actively developing:
- Enhanced GitLab integration with user-specific operations
- Improved JWT middleware with consistent session handling
- Database connection management optimization
- System connection management for external integrations

## Important Files and Entry Points

- Application entry: `src/main.py`
- API routes: `src/api/routers/`
- Use case implementations: `src/usecases/`
- Database models: `src/infrastructure/postgresql/models/`
- Configuration: `src/shared/config.py`
- Exceptions: `src/domain/exceptions/`