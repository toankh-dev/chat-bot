.PHONY: help install dev test coverage lint format clean docker-build docker-run deploy

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make dev               - Run development server"
	@echo "  make test              - Run tests"
	@echo "  make coverage          - Run tests with coverage"
	@echo "  make lint              - Run linters"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make docker-build      - Build Docker image"
	@echo "  make docker-run        - Run Docker container"
	@echo "  make deploy            - Deploy to AWS"
	@echo ""
	@echo "Database commands:"
	@echo "  make db-migrate        - Run migrations"
	@echo "  make db-rollback       - Rollback last migration"
	@echo "  make db-reset          - Reset database (drop all + migrate)"
	@echo "  make db-reset-seed     - Reset database (auto-seeds)"
	@echo ""
	@echo "Service commands:"
	@echo "  make services-up       - Start local services (Docker)"
	@echo "  make services-down     - Stop local services"
	@echo "  make services-logs     - View service logs"

install:
	pip install -r requirements.txt
	pre-commit install

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

coverage:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/
	mypy src/

format:
	black src/
	isort src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ htmlcov/ .coverage

docker-build:
	docker build -t ai-backend-api:latest -f docker/Dockerfile .

docker-run:
	docker run -p 8000:8000 --env-file .env ai-backend-api:latest

deploy:
	cd infra/terraform && terraform apply -var-file=environments/prod/terraform.tfvars

# Database commands
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head
	@echo "✓ Migrations completed"

db-rollback:
	@echo "Rolling back last migration..."
	alembic downgrade -1
	@echo "✓ Rollback completed"

db-reset:
	@echo "Resetting database..."
	alembic downgrade base
	alembic upgrade head
	@echo "✓ Database reset completed"

db-reset-seed: db-reset
	@echo "✓ Database reset and seeded successfully (seeds included in migration)"

db-create-migration:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Local services
services-up:
	docker-compose up -d

services-down:
	docker-compose down

services-logs:
	docker-compose logs -f
