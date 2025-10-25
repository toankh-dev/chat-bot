FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download model at build time (optional - WARNING: Large download ~14GB)
# Uncomment this to bake model into image (increases image size significantly)
# RUN python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
#     AutoModelForCausalLM.from_pretrained('stabilityai/japanese-stablelm-instruct-alpha-7b-v2', device_map='cpu'); \
#     AutoTokenizer.from_pretrained('stabilityai/japanese-stablelm-instruct-alpha-7b-v2')"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
