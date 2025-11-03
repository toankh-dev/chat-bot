# Build Lambda Layers for KASS Chatbot
# This script builds Lambda layers with dependencies for Python 3.11

param(
    [switch]$Clean,
    [switch]$Help
)

if ($Help) {
    Write-Host "Lambda Layers Build Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\build-layers.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Clean    Clean build directories before building" -ForegroundColor White
    Write-Host "  -Help     Show this help message" -ForegroundColor White
    Write-Host ""
    exit 0
}

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
$DIST_DIR = Join-Path $PROJECT_ROOT "terraform\dist\layers"
$TEMP_DIR = Join-Path $env:TEMP "lambda-layers-build"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Lambda Layers Build Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Clean if requested
if ($Clean -and (Test-Path $DIST_DIR)) {
    Write-Host "Cleaning dist directory..." -ForegroundColor Yellow
    Remove-Item -Path $DIST_DIR -Recurse -Force
}

# Create directories
Write-Host "Creating build directories..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $DIST_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $TEMP_DIR | Out-Null

# Function to build a layer
function Build-Layer {
    param(
        [string]$LayerName,
        [string[]]$Packages
    )

    Write-Host ""
    Write-Host "Building layer: $LayerName" -ForegroundColor Cyan
    Write-Host "Packages: $($Packages -join ', ')" -ForegroundColor Gray

    $layerDir = Join-Path $TEMP_DIR $LayerName
    $pythonDir = Join-Path $layerDir "python"

    # Clean layer directory
    if (Test-Path $layerDir) {
        Remove-Item -Path $layerDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null

    # Create requirements.txt
    $reqFile = Join-Path $layerDir "requirements.txt"
    $Packages | Out-File -FilePath $reqFile -Encoding utf8

    Write-Host "Installing packages..." -ForegroundColor Yellow

    # Install packages
    try {
        python -m pip install --quiet --upgrade pip
        python -m pip install `
            --target $pythonDir `
            --platform manylinux2014_x86_64 `
            --implementation cp `
            --python-version 3.11 `
            --only-binary=:all: `
            --upgrade `
            -r $reqFile

        Write-Host "Packages installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Some packages may require manual installation" -ForegroundColor Yellow
        Write-Host $_.Exception.Message -ForegroundColor Red
    }

    # Create ZIP
    $zipFile = Join-Path $DIST_DIR "$LayerName.zip"
    Write-Host "Creating ZIP: $zipFile" -ForegroundColor Yellow

    Push-Location $layerDir
    try {
        if (Test-Path $zipFile) {
            Remove-Item $zipFile -Force
        }

        # Use PowerShell compression
        Compress-Archive -Path "python" -DestinationPath $zipFile -CompressionLevel Optimal

        $zipSize = (Get-Item $zipFile).Length / 1MB
        Write-Host "Layer created: $LayerName ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# # Build Layer 1: Common Utilities
# Write-Host ""
# Write-Host "========================================" -ForegroundColor Magenta
# Write-Host "Layer 1: Common Utilities" -ForegroundColor Magenta
# Write-Host "========================================" -ForegroundColor Magenta

# $commonPackages = @(
#     "boto3==1.34.158",
#     "botocore==1.34.158",
#     "opensearch-py==2.4.0",
#     "requests-aws4auth==1.2.3",
#     "requests==2.31.0",
#     "python-dotenv==1.0.0",
#     "urllib3<2"
# )

# Build-Layer -LayerName "common-utilities" -Packages $commonPackages

# Build Layer 2: LangChain
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "Layer 2: LangChain" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

$langchainPackages = @(
    "langchain==0.1.20",
    "langchain-community==0.0.38",
    "langchain-core==0.1.52",
    "langchain-aws==0.1.0",
    "pydantic==2.7.1"
)

Build-Layer -LayerName "langchain" -Packages $langchainPackages

# # Build Layer 3: Document Processing
# Write-Host ""
# Write-Host "========================================" -ForegroundColor Magenta
# Write-Host "Layer 3: Document Processing" -ForegroundColor Magenta
# Write-Host "========================================" -ForegroundColor Magenta

# $docProcessingPackages = @(
#     "pypdf==3.17.0",
#     "python-docx==1.1.0",
#     "openpyxl==3.1.2",
#     "pandas==2.1.4",
#     "numpy==1.26.4"
# )

# Build-Layer -LayerName "document-processing" -Packages $docProcessingPackages

# Clean up temp directory
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
if (Test-Path $TEMP_DIR) {
    Remove-Item -Path $TEMP_DIR -Recurse -Force
}

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Lambda layers built in: $DIST_DIR" -ForegroundColor Cyan
Write-Host ""
Write-Host "Layers created:" -ForegroundColor Yellow
Get-ChildItem -Path $DIST_DIR -Filter "*.zip" | ForEach-Object {
    $size = $_.Length / 1MB
    Write-Host "  - $($_.Name) ($([math]::Round($size, 2)) MB)" -ForegroundColor White
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Upload layers to AWS: python scripts/lambda/deploy-layers.py" -ForegroundColor White
Write-Host "  2. Update Lambda functions to use layers" -ForegroundColor White
Write-Host ""
