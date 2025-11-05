#!/bin/bash
# Script to start all services and run migrations

set -e

echo "========================================="
echo "Starting AI Backend Services"
echo "========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Stop any existing containers
echo ""
echo "[1/5] Stopping existing containers..."
docker-compose down

# Start services
echo ""
echo "[2/5] Starting services (PostgreSQL, DynamoDB, Redis)..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo ""
echo "[3/5] Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
until docker exec ai-backend-postgres pg_isready -U postgres > /dev/null 2>&1; do
    sleep 1
    counter=$((counter+1))
    if [ $counter -ge $timeout ]; then
        echo "Error: PostgreSQL failed to start within $timeout seconds"
        docker-compose logs postgres
        exit 1
    fi
    echo -n "."
done
echo " Ready!"

# Run database migrations
echo ""
echo "[4/5] Running database migrations..."
sleep 2
alembic upgrade head

# Show status
echo ""
echo "[5/5] Checking service status..."
docker-compose ps

echo ""
echo "========================================="
echo "Services Started Successfully!"
echo "========================================="
echo ""
echo "Service URLs:"
echo "  PostgreSQL:  localhost:5432"
echo "  DynamoDB:    localhost:8001"
echo "  Redis:       localhost:6379"
echo ""
echo "Database credentials:"
echo "  Database: ai_backend"
echo "  User:     postgres"
echo "  Password: postgres"
echo ""
echo "To start the API server, run:"
echo "  make dev"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
