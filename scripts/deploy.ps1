# Simple wrapper for unified deployment script
# Usage: .\scripts\deploy.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Embedding System Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Set AWS LocalStack endpoint
$env:AWS_ENDPOINT_URL = "http://localhost:4566"
$env:AWS_DEFAULT_REGION = "ap-southeast-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"

# Run unified deployment script
python scripts\deploy.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
} else {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "✗ Deployment Failed" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
    exit 1
}
