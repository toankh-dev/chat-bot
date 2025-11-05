# ==============================================================================
# Multi-stage Dockerfile for KASS Chatbot API
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Base Python Image
# ------------------------------------------------------------------------------
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# ------------------------------------------------------------------------------
# Stage 2: Dependencies
# ------------------------------------------------------------------------------
FROM base as dependencies

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt ./
COPY lambda_functions/common/requirements.txt ./lambda_requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r lambda_requirements.txt && \
    pip install \
        fastapi==0.109.0 \
        uvicorn[standard]==0.27.0 \
        pydantic==2.5.3 \
        pydantic-settings==2.1.0 \
        python-jose[cryptography]==3.3.0 \
        passlib[bcrypt]==1.7.4 \
        python-multipart==0.0.6 \
        boto3==1.34.34 \
        psycopg2-binary==2.9.9 \
        redis==5.0.1 \
        chromadb==0.4.24 \
        langchain==0.1.4 \
        langchain-community==0.0.17 \
        opensearch-py==2.4.2

# ------------------------------------------------------------------------------
# Stage 3: Application
# ------------------------------------------------------------------------------
FROM base as application

# Set working directory
WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY . /app/

# Create directories for data
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
