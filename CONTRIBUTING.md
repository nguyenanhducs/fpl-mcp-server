# Contributing to FPL MCP Server

Thank you for considering contributing to the FPL MCP Server! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- `uv` package manager ([installation instructions](https://github.com/astral-sh/uv))

### Development Setup

1. **Fork and Clone**

   ```bash
   git clone https://github.com/nguyenanhducs/fpl-mcp-server.git
   cd fpl-mcp
   ```

2. **Install Dependencies**

   ```bash
   uv sync --extra dev
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_state.py

# Run only unit tests
uv run pytest -m unit
```

### Code Quality

**Linting and Formatting:**

```bash
# Run ruff linter
uv run ruff check src tests

# Auto-fix issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests
```

### Pre-commit Hooks

We use `pre-commit` to verify code quality before committing changes.

Setup:
```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install
```

Now checks will run automatically on commit. To run them manually on all files:
```bash
pre-commit run --all-files
```

### Running Locally

```bash
# Start the server (it will wait for MCP protocol messages on stdin)
uv run python -m src.main

# You should see:
# Starting FPL MCP Server...
# Imports successful. Initializing MCP server...
# Starting MCP Server (Stdio)...
#
# This means it's working! The server is now listening for MCP messages.
# Press Ctrl+C to stop it.
```

**To actually use the server**, configure it in Claude (see the [installation guidelines](docs/installation.md)) or use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) for debugging:

```bash
npx @modelcontextprotocol/inspector uv --directory <path-to-repo> run python -m src.main
```

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include examples in docstrings for complex functions

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use descriptive test names
- Group related tests in classes

## Reporting Bugs

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

## Feature Requests

For feature requests:

- Describe the use case
- Explain why it would be useful
- Suggest possible implementation (optional)

## Questions?

- Check existing issues and discussions
- Create a new issue with the `question` label

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉
