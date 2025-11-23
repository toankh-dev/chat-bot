# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KASS AI Backend System is an enterprise-grade AI chatbot backend built with Python and FastAPI, implementing Clean Architecture principles. It provides real-time WebSocket AI chat capabilities with RAG (Retrieval-Augmented Generation), multi-tenant workspaces, and external integrations (GitLab, Slack, Backlog).

## Architecture

The codebase follows Clean Architecture with these layers:

```
src/
├── api/                    # Presentation Layer - REST API controllers, WebSocket handlers, JWT middleware
├── application/           # Application Layer - Business logic services (20+ services)
├── usecases/             # Use Case Layer - Specific business use cases orchestrating logic (40+ use cases)
├── domain/               # Domain Layer - Core business entities (17 entities), value objects, business rules
├── infrastructure/       # Infrastructure Layer - PostgreSQL, AWS services, AI providers, vector stores
└── shared/               # Shared Interfaces - Repository interfaces, service interfaces, types
```

Key architectural principles:
- **Dependency inversion**: Repository interfaces in `shared/` implemented in `infrastructure/`
- **Dependency injection**: Comprehensive DI container in `src/core/dependencies.py` (800+ lines) - single source of truth for all dependencies
- **Use cases orchestrate**: Business logic flows from controllers → use cases → services → repositories
- **Domain entities contain business logic**: Infrastructure handles technical concerns only
- **Factory pattern**: AI services (LLMFactory, EmbeddingFactory, VectorStoreFactory) enable provider swapping without code changes

### Multi-Tenant Architecture

- All data scoped to workspaces for tenant isolation
- RBAC with admin/user roles
- Group-based access: Users → Groups → Chatbots
- User-specific external service connections (GitLab, Slack) with encrypted credentials

### Database Strategy

**Dual async/sync approach**:
- **Async** (`postgresql+asyncpg://`): All API operations for non-blocking I/O
- **Sync** (`postgresql://`): Alembic migrations and seeding scripts

**Connection pooling** (`src/infrastructure/postgresql/connection/database.py`):
- Pool size: 20 base connections, 30 max overflow
- Recycle: 1 hour to prevent stale connections
- DatabaseManager singleton with both async and sync session factories
- Intelligent session management: auto-commit on write operations (checks `dirty`/`new`/`deleted`), rollback on error

## Common Development Commands

### Running the Application

#### Option 1: Docker Compose (RECOMMENDED)
Includes all services: API, PostgreSQL, Redis, ChromaDB

```bash
# Start all services (API container name: ai-backend-api)
docker-compose up -d

# View API logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

#### Option 2: Development Server (Local)
Requires PostgreSQL, Redis, ChromaDB running separately

```bash
# Run with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Direct Python Execution
```bash
python src/main.py
```

### Docker Compose Operations

When running via Docker Compose, use these commands to interact with the API container:

```bash
# Shell access
docker-compose exec api /bin/bash

# Python interactive shell
docker-compose exec api python

# View real-time logs
docker-compose logs -f api

# Restart API container only
docker-compose restart api
```

### Database Operations

#### Local Execution
```bash
# Create migration (uses timestamp-based naming: YYYY_MM_DD_HHMM-hash-slug)
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Seed database with test data
python alembic/seed.py
# Creates test accounts:
#   - Admin: admin@kass.dev / admin123
#   - User: user@kass.dev / user123
```

#### Docker Compose Execution
```bash
# Create migration
docker-compose exec api alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1

# Seed database
docker-compose exec api python alembic/seed.py

# Direct database access
docker-compose exec postgres psql -U postgres -d ai_backend
```

### Testing

#### Local Execution
```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test suite
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only

# Run specific test file
pytest tests/unit/test_gitlab_service.py -v

# Run tests matching pattern
pytest tests/ -k gitlab -v

# Debug with print statements visible
pytest tests/ -s

# Debug with pdb breakpoint
pytest tests/ --pdb

# Re-run only failed tests from last run
pytest --lf
```

#### Docker Compose Execution
```bash
# Run all tests
docker-compose exec api pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test suite
docker-compose exec api pytest tests/unit/ -v
docker-compose exec api pytest tests/integration/ -v

# Run with pattern matching
docker-compose exec api pytest tests/ -k gitlab -v

# Debug mode
docker-compose exec api pytest tests/ -s
```

### Code Quality

#### Local Execution
```bash
# Format code (line length: 100)
black src/

# Sort imports (Black profile)
isort src/ --profile black

# Lint
flake8 src/ --max-line-length=100 --extend-ignore=E203,W503

# Type check (strict mode enabled)
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

#### Docker Compose Execution
```bash
# Format code
docker-compose exec api black src/

# Sort imports
docker-compose exec api isort src/ --profile black

# Lint
docker-compose exec api flake8 src/ --max-line-length=100 --extend-ignore=E203,W503

# Type check
docker-compose exec api mypy src/

# Run all tools together
docker-compose exec api sh -c "black src/ && isort src/ --profile black && flake8 src/ --max-line-length=100"
```

## Key Technical Details

### AI Provider Strategy (Multi-Provider)

**Development** (no AWS required):
```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/embedding-001  # 768 dimensions
VECTOR_STORE_PROVIDER=chromadb
FILE_STORAGE_PROVIDER=local
```

**Production**:
```env
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
EMBEDDING_MODEL=amazon.titan-embed-text-v1  # 1536 dimensions
VECTOR_STORE_PROVIDER=s3
FILE_STORAGE_PROVIDER=s3
```

Factory pattern enables seamless switching:
- `LLMFactory.create()` - Auto-selects provider based on LLM_PROVIDER
- `EmbeddingFactory.create()` - Matches LLM provider automatically
- `VectorStoreFactory.create()` - ChromaDB (local) or S3 (production)

### RAG Pipeline

Document processing flow: **Upload → Parse → Chunk → Embed → Index**

1. **Upload**: Files stored in local storage or S3
2. **Parse**: LangChain document loaders extract text
3. **Chunk**:
   - Code files: Specialized code chunking (excludes tests, configs, binaries)
   - Documents: Semantic chunking with overlap
4. **Embed**: Provider-specific embeddings (Gemini 768-dim or Titan 1536-dim)
5. **Index**: Vector store (ChromaDB or S3) with domain collections (healthcare, finance, general, gitlab)

Retrieval uses semantic search with top-k relevant chunks for AI context.

### Authentication & Authorization

**JWT-based** with HTTPBearer scheme:
- Middleware: `src/api/middlewares/jwt_middleware.py`
- Algorithm: HS256
- Access token: 30 minutes, Refresh token: 7 days
- Flow: Extract token → Validate → Lookup user → Check active status → Inject into request

Dependency injection for route protection:
```python
current_user: UserEntity = Depends(get_current_user)  # Any authenticated user
admin_user: UserEntity = Depends(require_admin)       # Admin role required
```

**Session consistency**: Use `x-session-id` header for session parameter consistency.

### External Integrations

**GitLab** (most comprehensive):
- Incremental sync: Tracks commits to avoid re-processing entire repos
- Code file filtering: Excludes tests, configs, binary files
- Repository/branch/commit tracking in database
- User-scoped connectors: Each user can have their own GitLab tokens
- Encrypted credentials: Fernet encryption for stored tokens

**Slack**: Message history import

**Backlog**: Project data synchronization

All connectors use user-specific credentials stored in `user_connections` table.

### API Structure

**REST API**:
- Base path: `/api/v1/`
- 11 router modules (auth, users, groups, chatbots, conversations, documents, gitlab, connectors, ai-models, etc.)
- OpenAPI docs: `/docs` (development only)
- Health check: `/health`

**WebSocket**:
- Endpoint: `/ws/chat`
- Real-time AI streaming responses
- Connection management in `src/api/controllers/chat_controller.py`
- Message queue processing for async operations

**Error handling**:
- Structured exception hierarchy in `src/core/errors.py`
- Domain-specific exceptions (15+ types)
- Consistent JSON error responses with error codes

### File Storage

**Local** (development):
```
./local_storage/documents/{domain}/{user_id}/filename
```

**S3** (production):
- Bucket-based organization
- Pre-signed URLs for downloads
- Automatic provider selection via FILE_STORAGE_PROVIDER

### Testing Infrastructure

**Test database strategy**:
1. Drop `ai_backend_test` database if exists
2. Create fresh test database
3. Run Alembic migrations (create all tables)
4. Run test with session auto-rollback
5. Drop all tables after test

**Fixtures** (`tests/conftest.py`):
- `db_engine` - Function-scoped fresh database
- `db_session` - Async session with auto-rollback
- `s3_service` - Mocked S3 to avoid AWS calls
- `sample_user_data`, `sample_chatbot_data` - Test data

**Mock external dependencies**: All AWS services (S3, Bedlog, Bedrock) and AI APIs mocked in tests using `tests/mocks/`.

## Development Guidelines

### When Adding New Features

1. **Start with domain**: Create/update entities in `src/domain/entities/`
2. **Define interfaces**: Add repository interfaces in `src/shared/interfaces/repositories/`
3. **Implement repositories**: Create implementations in `src/infrastructure/postgresql/repositories/`
4. **Create use cases**: Add business logic orchestration in `src/usecases/`
5. **Add controllers**: Create HTTP handlers in `src/api/controllers/`
6. **Register routes**: Wire up in `src/api/routers/`
7. **Update DI container**: Add factory functions in `src/core/dependencies.py`
8. **Write tests**: Unit tests for domain/use cases, integration tests for repositories, e2e for workflows

### Error Handling

- Use domain-specific exceptions from `src/domain/exceptions/`
- Controllers catch exceptions and convert to HTTP responses
- Always include error codes and user-friendly messages
- Global exception handler in `src/main.py` catches unhandled errors

### Database Migrations

- Alembic auto-formats migrations with Black
- Use descriptive slugs: `alembic revision --autogenerate -m "add_user_preferences_table"`
- Timestamp format: `2025_11_15_1430-a1b2c3d4-add_user_preferences_table.py`
- Always review auto-generated migrations before applying

## Important Entry Points

- **Application**: `src/main.py` - FastAPI app with middleware, routes, exception handlers
- **Configuration**: `src/core/config.py` - 60+ environment variables with Pydantic validation
- **DI Container**: `src/core/dependencies.py` - All repository/service/use case factories
- **Database Manager**: `src/infrastructure/postgresql/connection/database.py` - Singleton with async/sync sessions
- **Error Definitions**: `src/core/errors.py` - Exception hierarchy with HTTP status mapping
- **Seed Script**: `alembic/seed.py` - Creates admin/user, default group, chatbot, test conversations

## Current Development Focus

The `feature/refator` branch is actively developing:
- Enhanced GitLab integration with user-specific operations
- Improved JWT middleware with consistent session handling (`x-session-id` header)
- Database connection management optimization (pooling, session lifecycle)
- VectorStoreFactory refactoring for cleaner initialization
- System connection management for external integrations
