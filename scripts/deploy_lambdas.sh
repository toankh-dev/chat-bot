#!/bin/bash

# Deploy Lambda functions to LocalStack
# Usage: ./scripts/deploy_lambdas.sh

set -e

LOCALSTACK_ENDPOINT="http://localhost:4566"
AWS_REGION="ap-southeast-1"

echo "🚀 Deploying Lambda functions to LocalStack..."

# Function to package and deploy a Lambda
deploy_lambda() {
    local FUNCTION_NAME=$1
    local HANDLER=$2
    local RUNTIME=$3
    local DESCRIPTION=$4

    echo ""
    echo "📦 Packaging ${FUNCTION_NAME}..."

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)

    # Copy Lambda code
    cp -r "lambda/${FUNCTION_NAME}"/* "${TEMP_DIR}/"

    # Install dependencies if requirements.txt exists
    if [ -f "${TEMP_DIR}/requirements.txt" ]; then
        echo "   Installing dependencies..."
        pip install -r "${TEMP_DIR}/requirements.txt" -t "${TEMP_DIR}/" --quiet
    fi

    # Create zip file
    cd "${TEMP_DIR}"
    zip -r9 "/tmp/${FUNCTION_NAME}.zip" . > /dev/null
    cd - > /dev/null

    # Delete function if exists
    aws --endpoint-url="${LOCALSTACK_ENDPOINT}" \
        --region="${AWS_REGION}" \
        lambda delete-function \
        --function-name "${FUNCTION_NAME}" \
        2>/dev/null || true

    # Create Lambda function
    echo "   Deploying to LocalStack..."
    aws --endpoint-url="${LOCALSTACK_ENDPOINT}" \
        --region="${AWS_REGION}" \
        lambda create-function \
        --function-name "${FUNCTION_NAME}" \
        --runtime "${RUNTIME}" \
        --handler "${HANDLER}" \
        --role arn:aws:iam::000000000000:role/lambda-role \
        --zip-file "fileb:///tmp/${FUNCTION_NAME}.zip" \
        --description "${DESCRIPTION}" \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={LOCALSTACK_ENDPOINT=${LOCALSTACK_ENDPOINT}}" \
        > /dev/null

    # Cleanup
    rm -rf "${TEMP_DIR}"
    rm "/tmp/${FUNCTION_NAME}.zip"

    echo "   ✅ ${FUNCTION_NAME} deployed successfully"
}

# Deploy all Lambda functions
deploy_lambda "data_fetcher" "lambda_function.lambda_handler" "python3.11" "Fetch data from GitLab, Slack, and Backlog"
deploy_lambda "chat_handler" "lambda_function.lambda_handler" "python3.11" "Handle chat requests and orchestrate agents"
deploy_lambda "orchestrator_actions" "lambda_function.lambda_handler" "python3.11" "Orchestrator actions for multi-agent coordination"
deploy_lambda "report_actions" "lambda_function.lambda_handler" "python3.11" "Generate and post reports to external services"
deploy_lambda "summarize_actions" "lambda_function.lambda_handler" "python3.11" "Summarize conversations and documents"
deploy_lambda "code_review_actions" "lambda_function.lambda_handler" "python3.11" "Perform code reviews and analysis"
deploy_lambda "discord_fetcher" "lambda_function.lambda_handler" "python3.11" "Fetch data from Discord channels"

echo ""
echo "🎉 All Lambda functions deployed successfully!"
echo ""
echo "📋 List of deployed functions:"
aws --endpoint-url="${LOCALSTACK_ENDPOINT}" \
    --region="${AWS_REGION}" \
    lambda list-functions \
    --query 'Functions[].FunctionName' \
    --output table
