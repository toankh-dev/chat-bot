# PowerShell Script: Package Lambda Functions
# Creates deployment packages for Lambda functions

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Packaging Lambda Functions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
$DIST_DIR = Join-Path $ROOT_DIR "dist" "functions"

# Create dist directory
if (!(Test-Path $DIST_DIR)) {
    New-Item -ItemType Directory -Path $DIST_DIR -Force | Out-Null
}

# Lambda functions to package
$FUNCTIONS = @(
    "orchestrator",
    "vector_search",
    "document_processor"
)

# ============================================================================
# Package each Lambda function
# ============================================================================

foreach ($FUNCTION in $FUNCTIONS) {
    Write-Host ""
    Write-Host "Packaging $FUNCTION..." -ForegroundColor Yellow

    $FUNCTION_DIR = Join-Path $ROOT_DIR $FUNCTION
    $TEMP_DIR = Join-Path $DIST_DIR "temp_$FUNCTION"
    $ZIP_FILE = Join-Path $DIST_DIR "$FUNCTION.zip"

    # Check if function directory exists
    if (!(Test-Path $FUNCTION_DIR)) {
        Write-Host "Warning: Function directory not found: $FUNCTION_DIR" -ForegroundColor Yellow
        Write-Host "Skipping $FUNCTION" -ForegroundColor Yellow
        continue
    }

    # Clean temp directory
    if (Test-Path $TEMP_DIR) {
        Remove-Item -Recurse -Force $TEMP_DIR
    }
    New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null

    # Copy function code
    Write-Host "  Copying function code..."
    Copy-Item -Path (Join-Path $FUNCTION_DIR "*.py") -Destination $TEMP_DIR -Force

    # Copy requirements.txt if exists
    $REQ_FILE = Join-Path $FUNCTION_DIR "requirements.txt"
    if (Test-Path $REQ_FILE) {
        Copy-Item -Path $REQ_FILE -Destination $TEMP_DIR -Force
    }

    # Create zip
    Write-Host "  Creating $FUNCTION.zip..."
    if (Test-Path $ZIP_FILE) {
        Remove-Item -Force $ZIP_FILE
    }

    # Use PowerShell Compress-Archive
    $FILES_TO_ZIP = Get-ChildItem -Path $TEMP_DIR -File
    if ($FILES_TO_ZIP.Count -gt 0) {
        # Need to change directory to create zip with correct structure
        Push-Location $TEMP_DIR
        Compress-Archive -Path "*" -DestinationPath $ZIP_FILE -Force
        Pop-Location

        $ZIP_SIZE_KB = [math]::Round((Get-Item $ZIP_FILE).Length / 1KB, 2)
        Write-Host "  Created: $FUNCTION.zip ($ZIP_SIZE_KB KB)" -ForegroundColor Green
    } else {
        Write-Host "  Warning: No files found to package" -ForegroundColor Yellow
    }

    # Clean up temp directory
    Remove-Item -Recurse -Force $TEMP_DIR
}

# ============================================================================
# Summary
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Lambda Functions Packaged Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Packages created in: $DIST_DIR" -ForegroundColor Cyan
Write-Host ""

Get-ChildItem -Path $DIST_DIR -Filter "*.zip" | ForEach-Object {
    $size_kb = [math]::Round($_.Length / 1KB, 2)
    Write-Host "  - $($_.Name) ($size_kb KB)" -ForegroundColor White
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Ensure layers are built (run .\build_layers.ps1)" -ForegroundColor White
Write-Host "2. Update terraform/variables.tf with package paths" -ForegroundColor White
Write-Host "3. Run terraform apply to deploy" -ForegroundColor White
Write-Host ""
Write-Host "Note: Lambda functions will use layers for dependencies" -ForegroundColor Cyan
Write-Host "Make sure common utilities are available in the Lambda layer" -ForegroundColor Cyan
Write-Host ""
