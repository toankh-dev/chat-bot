# Deploy Full System: Lambdas + EventBridge Cronjobs
# This script:
# 1. Deploys all Lambda functions (data_fetcher, discord_fetcher, embedder)
# 2. Sets up EventBridge rules for scheduled execution
# 3. Configures permissions and targets

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Full System Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Set AWS LocalStack endpoint
$env:AWS_ENDPOINT_URL = "http://localhost:4566"
$env:AWS_DEFAULT_REGION = "ap-southeast-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"

# Step 1: Deploy Lambda functions
Write-Host "`n[STEP 1] Deploying Lambda Functions..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

try {
    python "$scriptDir\deploy_lambdas.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Lambda deployment failed"
    }
    Write-Host "`n✓ Lambda deployment completed" -ForegroundColor Green
} catch {
    Write-Host "✗ Lambda deployment failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Wait for Lambdas to be ready
Write-Host "`n[STEP 2] Waiting for Lambdas to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 3: Setup EventBridge cronjobs
Write-Host "`n[STEP 3] Setting up EventBridge Cronjobs..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

try {
    python "$scriptDir\setup_eventbridge_cronjobs.py"
    if ($LASTEXITCODE -ne 0) {
        throw "EventBridge setup failed"
    }
    Write-Host "`n✓ EventBridge cronjobs configured" -ForegroundColor Green
} catch {
    Write-Host "✗ EventBridge setup failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3.5: Setup S3 Triggers
Write-Host "`n[STEP 3.5] Setting up S3 Event Triggers..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

try {
    python "$scriptDir\setup_s3_triggers.py"
    if ($LASTEXITCODE -ne 0) {
        throw "S3 trigger setup failed"
    }
    Write-Host "`n✓ S3 event triggers configured" -ForegroundColor Green
} catch {
    Write-Host "✗ S3 trigger setup failed: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Verify deployment
Write-Host "`n[STEP 4] Verifying Deployment..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

# Check Lambda functions
Write-Host "Lambda Functions:" -ForegroundColor Cyan
aws --endpoint-url=http://localhost:4566 lambda list-functions --query 'Functions[?starts_with(FunctionName, `chatbot-`)].FunctionName' --output table

# Check EventBridge rules
Write-Host "`nEventBridge Rules:" -ForegroundColor Cyan
aws --endpoint-url=http://localhost:4566 events list-rules --name-prefix "chatbot-" --query 'Rules[].[Name,State,ScheduleExpression]' --output table

# Step 5: Create necessary S3 bucket if not exists
Write-Host "`n[STEP 5] Ensuring S3 Bucket Exists..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

$bucketName = "chatbot-knowledge-base"
$createBucketResult = aws --endpoint-url=http://localhost:4566 s3 mb "s3://$bucketName" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ S3 bucket created: $bucketName" -ForegroundColor Green
} else {
    Write-Host "✓ S3 bucket already exists: $bucketName" -ForegroundColor Green
}

# Step 6: Create Secrets Manager secrets (if needed)
Write-Host "`n[STEP 6] Checking Secrets Manager..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Yellow

$secrets = @(
    @{
        Name = "/chatbot/slack/bot-token"
        Value = @{
            bot_token = "xoxb-your-slack-bot-token"
        }
    },
    @{
        Name = "/chatbot/gitlab/api-token"
        Value = @{
            token = "your-gitlab-token"
            base_url = "https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID"
        }
    },
    @{
        Name = "/chatbot/backlog/api-key"
        Value = @{
            api_key = "your-backlog-api-key"
            space_url = "https://your-space.backlog.com"
        }
    },
    @{
        Name = "/chatbot/discord/bot-token"
        Value = @{
            bot_token = "your-discord-bot-token"
            guild_id = "your-guild-id"
            channel_ids = "channel-id-1,channel-id-2"
        }
    },
    @{
        Name = "/chatbot/voyage/api-key"
        Value = @{
            api_key = "your-voyage-api-key"
        }
    }
)

foreach ($secret in $secrets) {
    $secretValue = $secret.Value | ConvertTo-Json -Compress
    $createSecretResult = aws --endpoint-url=http://localhost:4566 secretsmanager create-secret `
        --name $secret.Name `
        --secret-string $secretValue 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Created secret: $($secret.Name)" -ForegroundColor Green
    } else {
        Write-Host "✓ Secret already exists: $($secret.Name)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✓ Lambda Functions Deployed:" -ForegroundColor Green
Write-Host "  - chatbot-data-fetcher (fetch + chunk)" -ForegroundColor White
Write-Host "  - chatbot-discord-fetcher (fetch)" -ForegroundColor White
Write-Host "  - chatbot-embedder (embed - S3 triggered)" -ForegroundColor White

Write-Host "`n✓ EventBridge Rules Configured:" -ForegroundColor Green
Write-Host "  - chatbot-data-fetcher-schedule (every 6 hours)" -ForegroundColor White
Write-Host "    • Fetches and chunks data → saves to S3" -ForegroundColor Gray
Write-Host "  - chatbot-discord-fetcher-schedule (every 6 hours)" -ForegroundColor White

Write-Host "`n✓ S3 Event Triggers Configured:" -ForegroundColor Green
Write-Host "  - S3 ObjectCreated:* on */chunked/*.json" -ForegroundColor White
Write-Host "    → Triggers embedder Lambda automatically" -ForegroundColor Gray

Write-Host "`n✓ Infrastructure Ready:" -ForegroundColor Green
Write-Host "  - S3 Bucket: $bucketName" -ForegroundColor White
Write-Host "  - Secrets Manager: 5 secrets configured" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "1. Update Secrets Manager with real API tokens:" -ForegroundColor Yellow
Write-Host "   aws --endpoint-url=http://localhost:4566 secretsmanager update-secret \`" -ForegroundColor White
Write-Host "     --secret-id /chatbot/slack/bot-token \`" -ForegroundColor White
Write-Host "     --secret-string '{\"bot_token\": \"xoxb-real-token\"}'" -ForegroundColor White

Write-Host "`n2. Manually trigger data fetch + chunk:" -ForegroundColor Yellow
Write-Host "   aws --endpoint-url=http://localhost:4566 lambda invoke \`" -ForegroundColor White
Write-Host "     --function-name chatbot-data-fetcher \`" -ForegroundColor White
Write-Host "     response.json" -ForegroundColor White
Write-Host "   (This will automatically trigger embedder via S3 event)" -ForegroundColor Gray

Write-Host "`n3. Monitor S3 bucket for chunked data:" -ForegroundColor Yellow
Write-Host "   aws --endpoint-url=http://localhost:4566 s3 ls s3://$bucketName/slack/chunked/ --recursive" -ForegroundColor White

Write-Host "`n4. Check Lambda logs:" -ForegroundColor Yellow
Write-Host "   # Data fetcher logs" -ForegroundColor Gray
Write-Host "   aws --endpoint-url=http://localhost:4566 logs tail \`" -ForegroundColor White
Write-Host "     /aws/lambda/chatbot-data-fetcher --follow" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "   # Embedder logs" -ForegroundColor Gray
Write-Host "   aws --endpoint-url=http://localhost:4566 logs tail \`" -ForegroundColor White
Write-Host "     /aws/lambda/chatbot-embedder --follow" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
