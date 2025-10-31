# PowerShell Script: Build Lambda Layers
# Creates Lambda layers with Python dependencies

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Lambda Layers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR
$DIST_DIR = Join-Path $ROOT_DIR "dist" "layers"

# Create dist directory
if (!(Test-Path $DIST_DIR)) {
    New-Item -ItemType Directory -Path $DIST_DIR -Force | Out-Null
}

# ============================================================================
# Build Common Utilities Layer
# ============================================================================

Write-Host ""
Write-Host "Building common-utilities layer..." -ForegroundColor Yellow

$LAYER_DIR = Join-Path $DIST_DIR "common-utilities"
$PYTHON_DIR = Join-Path $LAYER_DIR "python"

# Clean and create directories
if (Test-Path $LAYER_DIR) {
    Remove-Item -Recurse -Force $LAYER_DIR
}
New-Item -ItemType Directory -Path $PYTHON_DIR -Force | Out-Null

# Install common dependencies
Write-Host "Installing common dependencies..."
$REQUIREMENTS_FILE = Join-Path $ROOT_DIR "common" "requirements.txt"

pip install -r $REQUIREMENTS_FILE -t $PYTHON_DIR --upgrade --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing common dependencies" -ForegroundColor Red
    exit 1
}

# Copy common utilities
Write-Host "Copying common utilities..."
$COMMON_DIR = Join-Path $ROOT_DIR "common"
Copy-Item -Path (Join-Path $COMMON_DIR "*.py") -Destination $PYTHON_DIR -Force

# Create zip
Write-Host "Creating common-utilities.zip..."
$ZIP_FILE = Join-Path $DIST_DIR "common-utilities.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

# Use PowerShell Compress-Archive
Compress-Archive -Path (Join-Path $LAYER_DIR "*") -DestinationPath $ZIP_FILE -Force

$ZIP_SIZE_MB = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host "Created: common-utilities.zip ($ZIP_SIZE_MB MB)" -ForegroundColor Green

# ============================================================================
# Build LangChain Layer
# ============================================================================

Write-Host ""
Write-Host "Building langchain layer..." -ForegroundColor Yellow

$LAYER_DIR = Join-Path $DIST_DIR "langchain"
$PYTHON_DIR = Join-Path $LAYER_DIR "python"

# Clean and create directories
if (Test-Path $LAYER_DIR) {
    Remove-Item -Recurse -Force $LAYER_DIR
}
New-Item -ItemType Directory -Path $PYTHON_DIR -Force | Out-Null

# Install LangChain dependencies
Write-Host "Installing LangChain dependencies..."

# Create temporary requirements file
$TEMP_REQUIREMENTS = Join-Path $DIST_DIR "langchain_requirements.txt"
@"
langchain==0.1.0
langchain-community==0.0.10
"@ | Out-File -FilePath $TEMP_REQUIREMENTS -Encoding utf8

pip install -r $TEMP_REQUIREMENTS -t $PYTHON_DIR --upgrade --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing LangChain dependencies" -ForegroundColor Red
    exit 1
}

Remove-Item $TEMP_REQUIREMENTS

# Create zip
Write-Host "Creating langchain.zip..."
$ZIP_FILE = Join-Path $DIST_DIR "langchain.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

Compress-Archive -Path (Join-Path $LAYER_DIR "*") -DestinationPath $ZIP_FILE -Force

$ZIP_SIZE_MB = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host "Created: langchain.zip ($ZIP_SIZE_MB MB)" -ForegroundColor Green

# ============================================================================
# Build Document Processing Layer
# ============================================================================

Write-Host ""
Write-Host "Building document-processing layer..." -ForegroundColor Yellow

$LAYER_DIR = Join-Path $DIST_DIR "document-processing"
$PYTHON_DIR = Join-Path $LAYER_DIR "python"

# Clean and create directories
if (Test-Path $LAYER_DIR) {
    Remove-Item -Recurse -Force $LAYER_DIR
}
New-Item -ItemType Directory -Path $PYTHON_DIR -Force | Out-Null

# Install document processing dependencies
Write-Host "Installing document processing dependencies..."

# Create temporary requirements file
$TEMP_REQUIREMENTS = Join-Path $DIST_DIR "document_requirements.txt"
@"
pypdf==3.17.0
python-docx==1.1.0
openpyxl==3.1.2
"@ | Out-File -FilePath $TEMP_REQUIREMENTS -Encoding utf8

pip install -r $TEMP_REQUIREMENTS -t $PYTHON_DIR --upgrade --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing document processing dependencies" -ForegroundColor Red
    exit 1
}

Remove-Item $TEMP_REQUIREMENTS

# Create zip
Write-Host "Creating document-processing.zip..."
$ZIP_FILE = Join-Path $DIST_DIR "document-processing.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

Compress-Archive -Path (Join-Path $LAYER_DIR "*") -DestinationPath $ZIP_FILE -Force

$ZIP_SIZE_MB = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host "Created: document-processing.zip ($ZIP_SIZE_MB MB)" -ForegroundColor Green

# ============================================================================
# Summary
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Lambda Layers Built Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Layers created in: $DIST_DIR" -ForegroundColor Cyan
Write-Host ""

Get-ChildItem -Path $DIST_DIR -Filter "*.zip" | ForEach-Object {
    $size_mb = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  - $($_.Name) ($size_mb MB)" -ForegroundColor White
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run .\package_lambdas.ps1 to package Lambda functions" -ForegroundColor White
Write-Host "2. Run terraform apply to deploy infrastructure" -ForegroundColor White
Write-Host ""
