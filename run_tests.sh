#!/bin/bash

# Test Runner Script for AI Backend System
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Backend - Test Runner            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Parse arguments
TEST_TYPE=${1:-all}
COVERAGE=${2:-yes}

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2

    echo -e "${YELLOW}Running $test_name...${NC}"

    if [ "$COVERAGE" = "yes" ]; then
        pytest "$test_path" \
            --cov=src \
            --cov-report=html \
            --cov-report=term \
            --cov-report=xml \
            -v
    else
        pytest "$test_path" -v
    fi
}

# Main test execution
case $TEST_TYPE in
    all)
        echo -e "${GREEN}Running ALL tests${NC}"
        run_tests "tests/" "All Tests"
        ;;

    unit)
        echo -e "${GREEN}Running UNIT tests${NC}"
        run_tests "tests/unit/" "Unit Tests"
        ;;

    integration)
        echo -e "${GREEN}Running INTEGRATION tests${NC}"
        run_tests "tests/integration/" "Integration Tests"
        ;;

    gitlab)
        echo -e "${GREEN}Running GITLAB tests${NC}"
        pytest tests/ -k gitlab -v
        ;;

    fast)
        echo -e "${GREEN}Running FAST tests (no coverage)${NC}"
        COVERAGE=no
        pytest tests/ -v
        ;;

    coverage)
        echo -e "${GREEN}Generating coverage report${NC}"
        pytest tests/ \
            --cov=src \
            --cov-report=html \
            --cov-report=term
        echo -e "${BLUE}Opening coverage report...${NC}"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            open htmlcov/index.html
        elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            start htmlcov/index.html
        else
            xdg-open htmlcov/index.html
        fi
        ;;

    failed)
        echo -e "${GREEN}Re-running FAILED tests${NC}"
        pytest --lf -v
        ;;

    *)
        echo -e "${RED}Unknown option: $TEST_TYPE${NC}"
        echo
        echo "Usage: ./run_tests.sh [option]"
        echo
        echo "Options:"
        echo "  all         - Run all tests (default)"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  gitlab      - Run GitLab-related tests only"
        echo "  fast        - Run tests without coverage"
        echo "  coverage    - Generate and open coverage report"
        echo "  failed      - Re-run only failed tests"
        echo
        exit 1
        ;;
esac

# Check test result
if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}✅ Tests passed successfully!${NC}"

    if [ "$COVERAGE" = "yes" ]; then
        echo -e "${BLUE}📊 Coverage report: htmlcov/index.html${NC}"
    fi
else
    echo
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
