# =============================================================================
# Build All Lambda Packages (Functions + Layers)
# Unified script for KASS Chatbot Lambda deployment
# =============================================================================

param(
    [switch]$SkipLayers,
    [switch]$SkipFunctions,
    [switch]$Clean
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Lambda Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get directories - handles being called from scripts/lambda/
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
$TERRAFORM_DIR = Join-Path $ROOT "terraform"
$DIST = Join-Path $TERRAFORM_DIR "dist"

Write-Host "Root: $ROOT" -ForegroundColor Gray
Write-Host "Dist: $DIST" -ForegroundColor Gray
Write-Host ""

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning dist directory..." -ForegroundColor Yellow
    if (Test-Path $DIST) {
        Remove-Item -Recurse -Force $DIST
    }
    Write-Host "Done!" -ForegroundColor Green
    Write-Host ""
}

# Create dist directory
New-Item -ItemType Directory -Force -Path "$DIST\layers" | Out-Null
New-Item -ItemType Directory -Force -Path "$DIST\functions" | Out-Null

# =============================================================================
# Build Lambda Layers
# =============================================================================

if (-not $SkipLayers) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Building Lambda Layers" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

# Build common layer
Write-Host "`nBuilding common-utilities layer..." -ForegroundColor Cyan
$layerDir = "$DIST\layers\common-utilities\python"
New-Item -ItemType Directory -Force -Path $layerDir | Out-Null

Copy-Item "$ROOT\lambda_functions\common\*" -Destination $layerDir -Recurse -Force

# Install dependencies
pip install boto3 opensearch-py requests -t $layerDir --quiet

# Zip layer
Compress-Archive -Path "$DIST\layers\common-utilities\*" -DestinationPath "$DIST\layers\common-utilities.zip" -Force

Write-Host "OK - common-utilities.zip created" -ForegroundColor Green

} # end if (-not $SkipLayers)

# =============================================================================
# Build Lambda Functions
# =============================================================================

if (-not $SkipFunctions) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  Building Lambda Functions" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

# Build orchestrator function
Write-Host "`nBuilding orchestrator function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\orchestrator"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

Copy-Item "$ROOT\lambda_functions\orchestrator\handler.py" -Destination $funcDir -Force
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\orchestrator.zip" -Force

Write-Host "OK - orchestrator.zip created" -ForegroundColor Green

# Build vector_search function
Write-Host "`nBuilding vector_search function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\vector_search"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

Copy-Item "$ROOT\lambda_functions\vector_search\handler.py" -Destination $funcDir -Force
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\vector_search.zip" -Force

Write-Host "OK - vector_search.zip created" -ForegroundColor Green

# Build document_processor function
Write-Host "`nBuilding document_processor function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\document_processor"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

Copy-Item "$ROOT\lambda_functions\document_processor\handler.py" -Destination $funcDir -Force
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\document_processor.zip" -Force

Write-Host "OK - document_processor.zip created" -ForegroundColor Green

# Build report_tool function
Write-Host "`nBuilding report_tool function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\report_tool"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

if (Test-Path "$ROOT\lambda_functions\tools\report_tool") {
    Copy-Item "$ROOT\lambda_functions\tools\report_tool\*" -Destination $funcDir -Recurse -Force
} else {
    # Create placeholder
    "def handler(event, context): return {'statusCode': 200, 'body': 'Report tool'}" | Out-File "$funcDir\handler.py"
}
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\report_tool.zip" -Force

Write-Host "OK - report_tool.zip created" -ForegroundColor Green

# Build summarize_tool function
Write-Host "`nBuilding summarize_tool function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\summarize_tool"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

if (Test-Path "$ROOT\lambda_functions\tools\summarize_tool") {
    Copy-Item "$ROOT\lambda_functions\tools\summarize_tool\*" -Destination $funcDir -Recurse -Force
} else {
    # Create placeholder
    "def handler(event, context): return {'statusCode': 200, 'body': 'Summarize tool'}" | Out-File "$funcDir\handler.py"
}
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\summarize_tool.zip" -Force

Write-Host "OK - summarize_tool.zip created" -ForegroundColor Green

# Build code_review_tool function
Write-Host "`nBuilding code_review_tool function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\code_review_tool"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

if (Test-Path "$ROOT\lambda_functions\tools\code_review_tool") {
    Copy-Item "$ROOT\lambda_functions\tools\code_review_tool\*" -Destination $funcDir -Recurse -Force
} else {
    # Create placeholder
    "def handler(event, context): return {'statusCode': 200, 'body': 'Code review tool'}" | Out-File "$funcDir\handler.py"
}
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\code_review_tool.zip" -Force

Write-Host "OK - code_review_tool.zip created" -ForegroundColor Green

# Build discord_handler function
Write-Host "`nBuilding discord_handler function..." -ForegroundColor Cyan
$funcDir = "$DIST\functions\discord_handler"
New-Item -ItemType Directory -Force -Path $funcDir | Out-Null

if (Test-Path "$ROOT\lambda_functions\discord_handler") {
    Copy-Item "$ROOT\lambda_functions\discord_handler\*" -Destination $funcDir -Recurse -Force
} else {
    # Create placeholder
    "def handler(event, context): return {'statusCode': 200, 'body': 'Discord handler'}" | Out-File "$funcDir\handler.py"
}
Copy-Item "$ROOT\lambda_functions\common\*" -Destination $funcDir -Recurse -Force -ErrorAction SilentlyContinue

Compress-Archive -Path "$funcDir\*" -DestinationPath "$DIST\functions\discord_handler.zip" -Force

Write-Host "OK - discord_handler.zip created" -ForegroundColor Green

} # end if (-not $SkipFunctions)

# =============================================================================
# Summary
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Location: $DIST" -ForegroundColor Yellow

# List created files
Write-Host "`nCreated files:" -ForegroundColor Cyan
Get-ChildItem -Path $DIST -Recurse -Filter *.zip | ForEach-Object {
    $sizeInMB = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) - $sizeInMB MB"
}
