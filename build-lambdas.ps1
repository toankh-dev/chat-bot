# Wrapper script for building Lambda packages
# Forwards all parameters to the main build script

param(
    [switch]$SkipLayers,
    [switch]$SkipFunctions,
    [switch]$Clean,
    [switch]$Help
)

if ($Help) {
    Write-Host "Lambda Build Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\build-lambdas.ps1 [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -SkipLayers      Skip building Lambda layers" -ForegroundColor White
    Write-Host "  -SkipFunctions   Skip building Lambda functions" -ForegroundColor White
    Write-Host "  -Clean           Clean dist directory before building" -ForegroundColor White
    Write-Host "  -Help            Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\build-lambdas.ps1" -ForegroundColor White
    Write-Host "  .\build-lambdas.ps1 -SkipLayers" -ForegroundColor White
    Write-Host "  .\build-lambdas.ps1 -Clean" -ForegroundColor White
    Write-Host ""
    exit 0
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BUILD_SCRIPT = Join-Path $SCRIPT_DIR "scripts" | Join-Path -ChildPath "lambda" | Join-Path -ChildPath "build-all.ps1"

if (-not (Test-Path $BUILD_SCRIPT)) {
    Write-Host "Error: Build script not found at $BUILD_SCRIPT" -ForegroundColor Red
    exit 1
}

# Forward parameters to the main build script
& $BUILD_SCRIPT -SkipLayers:$SkipLayers -SkipFunctions:$SkipFunctions -Clean:$Clean
