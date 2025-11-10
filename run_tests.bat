@echo off
REM Test Runner Script for AI Backend System (Windows)
REM Usage: run_tests.bat [option]

setlocal enabledelayedexpansion

echo ╔════════════════════════════════════════╗
echo ║   AI Backend - Test Runner            ║
echo ╚════════════════════════════════════════╝
echo.

set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

REM Run tests based on type
if "%TEST_TYPE%"=="all" (
    echo Running ALL tests...
    pytest tests/ --cov=src --cov-report=html --cov-report=term --cov-report=xml -v
    goto :check_result
)

if "%TEST_TYPE%"=="unit" (
    echo Running UNIT tests...
    pytest tests/unit/ --cov=src --cov-report=html --cov-report=term -v
    goto :check_result
)

if "%TEST_TYPE%"=="integration" (
    echo Running INTEGRATION tests...
    pytest tests/integration/ --cov=src --cov-report=html --cov-report=term -v
    goto :check_result
)

if "%TEST_TYPE%"=="gitlab" (
    echo Running GITLAB tests...
    pytest tests/ -k gitlab -v
    goto :check_result
)

if "%TEST_TYPE%"=="fast" (
    echo Running FAST tests (no coverage)...
    pytest tests/ -v
    goto :check_result
)

if "%TEST_TYPE%"=="coverage" (
    echo Generating coverage report...
    pytest tests/ --cov=src --cov-report=html --cov-report=term
    echo Opening coverage report...
    start htmlcov\index.html
    goto :end
)

if "%TEST_TYPE%"=="failed" (
    echo Re-running FAILED tests...
    pytest --lf -v
    goto :check_result
)

REM Unknown option
echo Unknown option: %TEST_TYPE%
echo.
echo Usage: run_tests.bat [option]
echo.
echo Options:
echo   all         - Run all tests (default)
echo   unit        - Run unit tests only
echo   integration - Run integration tests only
echo   gitlab      - Run GitLab-related tests only
echo   fast        - Run tests without coverage
echo   coverage    - Generate and open coverage report
echo   failed      - Re-run only failed tests
echo.
exit /b 1

:check_result
if %errorlevel% equ 0 (
    echo.
    echo ✅ Tests passed successfully!
    echo 📊 Coverage report: htmlcov\index.html
) else (
    echo.
    echo ❌ Tests failed!
    exit /b 1
)

:end
endlocal
