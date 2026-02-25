# Testing Guide

## 📁 Test Structure

```
tests/
├── unit/                           # Unit tests (isolated component testing)
│   ├── test_gitlab_service.py      # GitLabService tests
│   ├── test_code_chunking_service.py  # CodeChunkingService tests
│   └── ...
├── integration/                    # Integration tests (API endpoints)
│   ├── test_gitlab_endpoints.py    # GitLab API endpoints
│   ├── test_document_processing_pipeline.py
│   └── ...
├── mocks/                          # Mock objects and utilities
│   └── embedding_service_mock.py
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Run Specific Test Suites

```bash
# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run only GitLab tests
pytest tests/ -k gitlab -v

# Run specific test file
pytest tests/unit/test_gitlab_service.py -v

# Run specific test class
pytest tests/unit/test_gitlab_service.py::TestGetProjectInfo -v

# Run specific test method
pytest tests/unit/test_gitlab_service.py::TestGetProjectInfo::test_get_project_info_success -v
```

---

## 📊 Coverage Goals

| Component | Current Coverage | Target | Status |
|-----------|------------------|--------|--------|
| GitLabService | TBD | ≥ 80% | ⏳ |
| CodeChunkingService | TBD | ≥ 80% | ⏳ |
| GitLabSyncService | TBD | ≥ 70% | ⏳ |
| GitLabController | TBD | ≥ 70% | ⏳ |
| Overall | TBD | ≥ 75% | ⏳ |

---

## 🧪 Unit Tests

Unit tests focus on testing individual components in isolation using mocks.

### Example: Testing GitLabService

```python
def test_filter_python_files(gitlab_service):
    """Test filtering Python files."""
    files = [
        "src/main.py",
        "tests/test_main.py",
        "README.md"
    ]

    result = gitlab_service.filter_code_files(files)

    assert "src/main.py" in result
    assert "tests/test_main.py" not in result  # Excluded
```

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src.infrastructure.external --cov=src.application.services
```

---

## 🔗 Integration Tests

Integration tests verify API endpoints and full workflows.

### Example: Testing GitLab Sync Endpoint

```python
def test_sync_repository_success(client, auth_headers):
    """Test successful repository sync."""
    payload = {
        "repo_url": "https://gitlab.com/user/test-repo",
        "branch": "main",
        "knowledge_base_id": "kb_gitlab",
        "group_id": "test-group"
    }

    response = client.post("/api/v1/gitlab/sync", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_gitlab_endpoints.py -v
```

---

## 🧰 Test Utilities

### Mocks

Located in `tests/mocks/`:

- **EmbeddingServiceMock** - Mock embedding generation (avoid API quota)
- **S3ServiceMock** - Mock S3 file storage

### Fixtures

Common fixtures defined in `conftest.py`:

- `db_session` - Database session
- `client` - FastAPI test client
- `mock_current_user` - Authenticated user
- `auth_headers` - JWT authentication headers

---

## 📝 Writing New Tests

### 1. Unit Test Template

```python
"""
Unit tests for YourService.
"""

import pytest
from src.your.module import YourService


@pytest.fixture
def your_service():
    """Create YourService instance."""
    return YourService()


class TestYourMethod:
    """Test your_method."""

    def test_success_case(self, your_service):
        """Test successful execution."""
        result = your_service.your_method("input")
        assert result == "expected"

    def test_error_case(self, your_service):
        """Test error handling."""
        with pytest.raises(ValueError):
            your_service.your_method("invalid")
```

### 2. Integration Test Template

```python
"""
Integration tests for Your API.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestYourEndpoint:
    """Test /api/v1/your/endpoint."""

    def test_endpoint_success(self, client, auth_headers):
        """Test successful request."""
        response = client.get("/api/v1/your/endpoint", headers=auth_headers)
        assert response.status_code == 200
```

---

## 🐛 Debugging Tests

### Run with verbose output

```bash
pytest tests/ -vv
```

### Run with print statements

```bash
pytest tests/ -s
```

### Run with debugger

```bash
pytest tests/ --pdb
```

### Run failed tests only

```bash
# First run
pytest tests/

# Re-run only failed tests
pytest --lf
```

---

## 🔧 Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### Running by markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

---

## 📈 Continuous Integration

Tests run automatically on:

- Every push to `main` branch
- Every pull request
- Nightly builds

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 🎯 Best Practices

### DO ✅

- Write descriptive test names
- Test both success and error cases
- Use fixtures for common setup
- Mock external dependencies
- Aim for high coverage (≥75%)
- Run tests before committing

### DON'T ❌

- Test implementation details
- Make tests depend on each other
- Use real API keys in tests
- Commit failing tests
- Skip error handling tests

---

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)

---

## 🆘 Need Help?

If tests are failing:

1. Check error message carefully
2. Run with `-vv` for more details
3. Check [Troubleshooting Guide](../docs/GITLAB_TESTING_GUIDE.md#troubleshooting)
4. Ask in #testing channel
5. Create GitHub issue
