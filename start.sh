#!/bin/bash

# Quick Start Script for Local Chatbot
# This script will setup and start all services

set -e

echo "======================================"
echo "🤖 Multi-Agent Chatbot - Local Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys:${NC}"
    echo "   - GITLAB_TOKEN"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - BACKLOG_API_KEY"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Check Docker
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check Docker Compose
echo "🔍 Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose is available${NC}"
echo ""

# Pull images
echo "📦 Pulling Docker images..."
docker-compose pull

# Start services
echo ""
echo "🚀 Starting services..."
echo -e "${YELLOW}⏳ This may take 15-45 minutes on first run (downloading models)${NC}"
echo ""

# Start LocalStack first
echo "1/6 Starting LocalStack..."
docker-compose up -d localstack
sleep 5

# Start ChromaDB
echo "2/6 Starting ChromaDB..."
docker-compose up -d chromadb
sleep 3

# Start PostgreSQL & Redis
echo "3/6 Starting PostgreSQL & Redis..."
docker-compose up -d postgres redis
sleep 3

# Start Embedding Service
echo "4/6 Starting Embedding Service (downloading ~500MB model)..."
docker-compose up -d embedding-service
echo -e "${YELLOW}⏳ Waiting for embedding service to download model...${NC}"

# Wait for embedding service
max_wait=300  # 5 minutes
elapsed=0
while ! curl -s http://localhost:8002/health > /dev/null 2>&1; do
    if [ $elapsed -ge $max_wait ]; then
        echo -e "${RED}❌ Embedding service failed to start${NC}"
        docker-compose logs embedding-service
        exit 1
    fi
    echo -n "."
    sleep 5
    elapsed=$((elapsed + 5))
done
echo ""
echo -e "${GREEN}✅ Embedding service is ready${NC}"

# Start LLM Service
echo "5/6 Starting LLM Service (downloading ~14GB model)..."
docker-compose up -d llm-service
echo -e "${YELLOW}⏳ Waiting for LLM service to download model... (this takes 10-30 minutes)${NC}"

# Wait for LLM service (longer timeout)
max_wait=1800  # 30 minutes
elapsed=0
while ! curl -s http://localhost:8003/health > /dev/null 2>&1; do
    if [ $elapsed -ge $max_wait ]; then
        echo -e "${RED}❌ LLM service failed to start${NC}"
        docker-compose logs llm-service
        exit 1
    fi
    if [ $((elapsed % 30)) -eq 0 ]; then
        echo -e "${YELLOW}Still downloading... ($elapsed seconds elapsed)${NC}"
    fi
    echo -n "."
    sleep 5
    elapsed=$((elapsed + 5))
done
echo ""
echo -e "${GREEN}✅ LLM service is ready${NC}"

# Start Main App
echo "6/6 Starting Main Application..."
docker-compose up -d app
sleep 5

echo ""
echo "======================================"
echo -e "${GREEN}✅ All services started!${NC}"
echo "======================================"
echo ""

# Show service status
echo "📊 Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LocalStack:        http://localhost:4566"
echo "ChromaDB:          http://localhost:8001"
echo "Embedding Service: http://localhost:8002"
echo "LLM Service:       http://localhost:8003"
echo "Main Application:  http://localhost:8000"
echo "PostgreSQL:        localhost:5432"
echo "Redis:             localhost:6379"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Initialize LocalStack
echo "🔧 Initializing LocalStack..."
if command -v python3 &> /dev/null; then
    python3 scripts/setup_localstack.py
    echo -e "${GREEN}✅ LocalStack initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Python3 not found. Please run manually:${NC}"
    echo "   python scripts/setup_localstack.py"
fi

echo ""
echo "======================================"
echo "🎉 Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Test the services:"
echo "   curl http://localhost:8000/health"
echo ""
echo "2. Ingest data (optional):"
echo "   python scripts/run_data_fetcher.py"
echo "   python scripts/build_vector_index.py"
echo ""
echo "3. Send a test query:"
echo "   curl -X POST http://localhost:8000/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Hello!\", \"conversation_id\": \"test-1\"}'"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop services:"
echo "   docker-compose down"
echo ""
echo "📖 Full documentation: LOCAL_SETUP_GUIDE.md"
echo ""
echo -e "${GREEN}Happy Chatting! 🤖${NC}"
