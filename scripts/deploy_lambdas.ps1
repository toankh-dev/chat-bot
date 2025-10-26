            # Deploy Lambda functions to LocalStack
# Usage: .\scripts\deploy_lambdas.ps1

$LOCALSTACK_ENDPOINT = "http://localhost:4566"
$AWS_REGION = "ap-southeast-1"

Write-Host "🚀 Deploying Lambda functions to LocalStack..." -ForegroundColor Green

function Deploy-Lambda {
    param(
        [string]$FunctionName,
        [string]$Handler,
        [string]$Runtime,
        [string]$Description
    )

    Write-Host ""
    Write-Host "📦 Packaging $FunctionName..." -ForegroundColor Yellow

    # Create temporary directory
    $TempDir = New-Item -ItemType Directory -Path "$env:TEMP\lambda_$FunctionName" -Force

    # Copy Lambda code
    Copy-Item -Path "lambda\$FunctionName\*" -Destination $TempDir -Recurse -Force

    # Install dependencies if requirements.txt exists
    if (Test-Path "$TempDir\requirements.txt") {
        Write-Host "   Installing dependencies..." -ForegroundColor Gray
        pip install -r "$TempDir\requirements.txt" -t $TempDir --quiet
    }

    # Create zip file
    $ZipFile = "$env:TEMP\$FunctionName.zip"
    if (Test-Path $ZipFile) { Remove-Item $ZipFile }

    Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipFile -CompressionLevel Optimal

    # Delete function if exists
    Write-Host "   Deleting old function if exists..." -ForegroundColor Gray
    aws --endpoint-url=$LOCALSTACK_ENDPOINT `
        --region=$AWS_REGION `
        lambda delete-function `
        --function-name $FunctionName `
        2>$null

    # Create Lambda function
    Write-Host "   Deploying to LocalStack..." -ForegroundColor Gray
    aws --endpoint-url=$LOCALSTACK_ENDPOINT `
        --region=$AWS_REGION `
        lambda create-function `
        --function-name $FunctionName `
        --runtime $Runtime `
        --handler $Handler `
        --role "arn:aws:iam::000000000000:role/lambda-role" `
        --zip-file "fileb://$ZipFile" `
        --description $Description `
        --timeout 300 `
        --memory-size 512 `
        --environment "Variables={LOCALSTACK_ENDPOINT=$LOCALSTACK_ENDPOINT}" `
        | Out-Null

    # Cleanup
    Remove-Item -Path $TempDir -Recurse -Force
    Remove-Item -Path $ZipFile -Force

    Write-Host "   ✅ $FunctionName deployed successfully" -ForegroundColor Green
}

# Deploy all Lambda functions
Deploy-Lambda -FunctionName "data_fetcher" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Fetch data from GitLab, Slack, and Backlog"
Deploy-Lambda -FunctionName "chat_handler" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Handle chat requests and orchestrate agents"
Deploy-Lambda -FunctionName "orchestrator_actions" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Orchestrator actions for multi-agent coordination"
Deploy-Lambda -FunctionName "report_actions" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Generate and post reports to external services"
Deploy-Lambda -FunctionName "summarize_actions" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Summarize conversations and documents"
Deploy-Lambda -FunctionName "code_review_actions" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Perform code reviews and analysis"
Deploy-Lambda -FunctionName "discord_fetcher" -Handler "lambda_function.lambda_handler" -Runtime "python3.11" -Description "Fetch data from Discord channels"

Write-Host ""
Write-Host "🎉 All Lambda functions deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 List of deployed functions:" -ForegroundColor Cyan
aws --endpoint-url=$LOCALSTACK_ENDPOINT `
    --region=$AWS_REGION `
    lambda list-functions `
    --query 'Functions[].FunctionName' `
    --output table
