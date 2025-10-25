@echo off
REM Quick Start Script for Local Chatbot (Windows)

echo ======================================
echo 🤖 Multi-Agent Chatbot - Local Setup
echo ======================================
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo ✅ Created .env file
    echo ⚠️  Please edit .env and add your API keys:
    echo    - GITLAB_TOKEN
    echo    - SLACK_BOT_TOKEN
    echo    - BACKLOG_API_KEY
    echo.
    pause
)

REM Check Docker
echo 🔍 Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)
echo ✅ Docker is running
echo.

REM Check Docker Compose
echo 🔍 Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found.
    pause
    exit /b 1
)
echo ✅ Docker Compose is available
echo.

REM Pull images
echo 📦 Pulling Docker images...
docker-compose pull
echo.

REM Start services
echo 🚀 Starting services...
echo ⏳ This may take 15-45 minutes on first run (downloading models)
echo.

echo 1/6 Starting LocalStack...
docker-compose up -d localstack
timeout /t 5 /nobreak >nul

echo 2/6 Starting ChromaDB...
docker-compose up -d chromadb
timeout /t 3 /nobreak >nul

echo 3/6 Starting PostgreSQL ^& Redis...
docker-compose up -d postgres redis
timeout /t 3 /nobreak >nul

echo 4/6 Starting Embedding Service (downloading ~500MB model)...
docker-compose up -d embedding-service
echo ⏳ Waiting for embedding service to download model...

REM Wait for embedding service
:wait_embedding
timeout /t 5 /nobreak >nul
curl -s http://localhost:8002/health >nul 2>&1
if errorlevel 1 goto wait_embedding
echo ✅ Embedding service is ready
echo.

echo 5/6 Starting LLM Service (downloading ~14GB model)...
docker-compose up -d llm-service
echo ⏳ Waiting for LLM service to download model... (this takes 10-30 minutes)

REM Wait for LLM service
:wait_llm
timeout /t 5 /nobreak >nul
curl -s http://localhost:8003/health >nul 2>&1
if errorlevel 1 (
    echo Still downloading...
    goto wait_llm
)
echo ✅ LLM service is ready
echo.

echo 6/6 Starting Main Application...
docker-compose up -d app
timeout /t 5 /nobreak >nul

echo.
echo ======================================
echo ✅ All services started!
echo ======================================
echo.

echo 📊 Service Status:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo LocalStack:        http://localhost:4566
echo ChromaDB:          http://localhost:8001
echo Embedding Service: http://localhost:8002
echo LLM Service:       http://localhost:8003
echo Main Application:  http://localhost:8000
echo PostgreSQL:        localhost:5432
echo Redis:             localhost:6379
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Initialize LocalStack
echo 🔧 Initializing LocalStack...
python scripts\setup_localstack.py
if errorlevel 1 (
    echo ⚠️  Failed to initialize LocalStack. Please run manually:
    echo    python scripts\setup_localstack.py
) else (
    echo ✅ LocalStack initialized
)

echo.
echo ======================================
echo 🎉 Setup Complete!
echo ======================================
echo.
echo 📝 Next steps:
echo.
echo 1. Test the services:
echo    curl http://localhost:8000/health
echo.
echo 2. Ingest data (optional):
echo    python scripts\run_data_fetcher.py
echo    python scripts\build_vector_index.py
echo.
echo 3. Send a test query:
echo    curl -X POST http://localhost:8000/chat ^
echo      -H "Content-Type: application/json" ^
echo      -d "{\"message\": \"Hello!\", \"conversation_id\": \"test-1\"}"
echo.
echo 4. View logs:
echo    docker-compose logs -f
echo.
echo 5. Stop services:
echo    docker-compose down
echo.
echo 📖 Full documentation: LOCAL_SETUP_GUIDE.md
echo.
echo Happy Chatting! 🤖
echo.
pause
