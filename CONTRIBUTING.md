# Contributing to AI Backend System

Thank you for your interest in contributing to the AI Backend System! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/chat-bot.git
   cd chat-bot
   ```

3. **Set up development environment**:
   ```bash
   make install
   ```

4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Process

### 1. Install Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run linters and formatters before each commit.

### 2. Run Tests Regularly

```bash
make test
```

### 3. Check Code Quality

```bash
make lint
make format
```

## Coding Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **type hints** for all function parameters and return values
- Maximum line length: **100 characters**
- Use **docstrings** for all public modules, classes, and functions

### Example Function Documentation

```python
async def create_user(
    username: str,
    email: str,
    password: str
) -> User:
    """
    Create a new user account.

    Args:
        username: Unique username for the account
        email: Valid email address
        password: Plain text password (will be hashed)

    Returns:
        User: The created user entity

    Raises:
        ValidationError: If input validation fails
        ResourceAlreadyExistsError: If user already exists
    """
    # Implementation here
    pass
```

### Code Organization

Follow the **Clean Architecture** pattern:

- **Domain Layer**: Pure business logic, no dependencies on external systems
- **Application Layer**: Use cases and business workflows
- **Infrastructure Layer**: External system integrations (databases, APIs)
- **Presentation Layer**: API controllers and WebSocket handlers

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `UserService`, `ChatbotController`)
- **Functions/Methods**: `snake_case` (e.g., `get_user`, `create_chatbot`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: Prefix with underscore (e.g., `_internal_method`)

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
├── integration/       # Integration tests (with dependencies)
└── e2e/              # End-to-end tests (full workflows)
```

### Writing Tests

- Use **pytest** framework
- Follow **Arrange-Act-Assert** pattern
- Use **descriptive test names** that explain what is being tested
- **Mock external dependencies** in unit tests
- Aim for **>80% code coverage** on critical paths

### Example Test

```python
import pytest
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.uuid_vo import UUID


def test_user_deactivation():
    """Test that user can be successfully deactivated."""
    # Arrange
    user = User(
        id=UUID.generate(),
        email=Email("test@example.com"),
        username="testuser",
        full_name="Test User",
        hashed_password="hashed"
    )

    # Act
    user.deactivate()

    # Assert
    assert user.is_active is False
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

## Pull Request Process

### 1. Before Submitting

- [ ] All tests pass
- [ ] Code is formatted with `black`
- [ ] No linting errors
- [ ] Type checking passes with `mypy`
- [ ] Documentation is updated
- [ ] Changelog is updated (if applicable)

### 2. Pull Request Description

Include the following in your PR description:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
```

### 3. Review Process

- At least **one approval** required
- All CI checks must pass
- Address all review comments
- Keep commits atomic and well-described

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(auth): Add JWT refresh token support

Implement refresh token functionality to allow users to
maintain sessions without re-authenticating.

Closes #123
```

```
fix(websocket): Handle connection timeout gracefully

Add timeout handling to prevent hanging WebSocket connections.

Fixes #456
```

## Architecture Decisions

### When to Add a New Service

Add a new service when:
- The functionality represents a distinct business capability
- It has clear boundaries and responsibilities
- It can be tested independently

### When to Add a New Repository

Add a new repository when:
- A new database table or DynamoDB table is introduced
- A distinct data access pattern emerges
- Separation improves testability

### When to Add a New Entity

Add a new domain entity when:
- It represents a core business concept
- It has identity and lifecycle
- It contains business logic that belongs to that concept

## Questions?

If you have questions about contributing, please:
- Check existing [GitHub Issues](https://github.com/your-org/chat-bot/issues)
- Create a new issue with the `question` label
- Reach out to maintainers

Thank you for contributing! 🎉
