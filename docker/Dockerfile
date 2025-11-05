# Multi-stage Dockerfile for AWS Lambda deployment
FROM public.ecr.aws/lambda/python:3.12 as builder

# Install build dependencies
RUN yum install -y gcc postgresql-devel python3-devel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -t /asset

# Final stage
FROM public.ecr.aws/lambda/python:3.12

# Copy installed dependencies from builder
COPY --from=builder /asset ${LAMBDA_TASK_ROOT}

# Copy application code
COPY src ${LAMBDA_TASK_ROOT}/src

# Set environment variables
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}"
ENV PYTHONUNBUFFERED=1

# Lambda handler
CMD ["src.lambda_handlers.api_handler.handler"]
