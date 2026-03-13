# Contributing to s3check

Thank you for your interest in contributing to s3check! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Adding New Providers](#adding-new-providers)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/s3check.git
   cd s3check
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/yannisduvignau/s3check.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv

### Setup Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode with all dependencies:
   ```bash
   make install-dev
   # or
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

2. Make your changes, following the [code style](#code-style) guidelines

3. Add tests for your changes in the `tests/` directory

4. Run the test suite to ensure everything works:
   ```bash
   make test
   ```

5. Commit your changes with a clear commit message:
   ```bash
   git commit -m "Add feature: brief description"
   ```

## Testing

### Running Tests

Run the full test suite:
```bash
make test
```

Run tests with coverage:
```bash
make test-cov
```

Run specific tests:
```bash
pytest tests/test_providers.py
pytest tests/test_client.py::test_run_checks_success
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Use pytest fixtures for common setup
- Mock external dependencies (boto3, network calls)
- Aim for high coverage of new code

Example test structure:
```python
import pytest
from s3check.providers import get_provider

def test_get_provider_by_id():
    """Test retrieving provider by numeric ID."""
    provider = get_provider("1")
    assert provider["name"] == "AWS S3"

def test_get_provider_by_cli_name():
    """Test retrieving provider by CLI name."""
    provider = get_provider("aws")
    assert provider["name"] == "AWS S3"
```

## Code Style

This project follows strict code style guidelines:

### Python Style

- **PEP 8** compliance (enforced by flake8)
- **Type hints** where applicable (checked by mypy)
- **Docstrings** for all public functions, classes, and modules
- **Line length**: 100 characters maximum
- **Import order**: stdlib, third-party, local (enforced by isort)

### Running Code Quality Checks

Format code automatically:
```bash
make format
```

Check formatting without changes:
```bash
make format-check
```

Run linters:
```bash
make lint
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of the function.
    
    More detailed description if needed.
    
    Args:
        param1 (str): Description of param1.
        param2 (int): Description of param2.
        
    Returns:
        bool: Description of return value.
        
    Raises:
        ValueError: When param1 is empty.
        
    Examples:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Submitting Changes

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub from your fork to the main repository

3. In your PR description:
   - Describe what changes you made and why
   - Reference any related issues (e.g., "Fixes #123")
   - Include screenshots for UI changes
   - Note any breaking changes

4. Wait for CI checks to pass

5. Address any feedback from reviewers

6. Once approved, your PR will be merged!

## Adding New Providers

To add support for a new S3-compatible provider:

1. Add the provider definition to [`src/s3check/providers.py`](src/s3check/providers.py):

```python
PROVIDERS = {
    # ... existing providers ...
    "8": {
        "name": "New Provider Name",
        "endpoint": "https://s3.{region}.newprovider.com",  # or "custom" or None
        "fields": ["access_key", "secret_key", "region", "bucket"],
        "region_default": "us-east-1",
    },
}
```

2. Update the CLI mapping:

```python
PROVIDER_CLI_MAP = {
    # ... existing mappings ...
    "newprovider": "8",
}
```

3. Add tests in `tests/test_providers.py`

4. Update the README with the new provider

5. Update the CLI help text in [`src/s3check/cli.py`](src/s3check/cli.py)

## Development Tips

### Useful Make Commands

- `make help` - Show all available commands
- `make install-dev` - Install with dev dependencies
- `make test` - Run tests
- `make lint` - Run linters
- `make format` - Auto-format code
- `make clean` - Remove build artifacts

### Debugging

To debug interactively with pdb:
```python
import pdb; pdb.set_trace()
```

Or use pytest with pdb:
```bash
pytest --pdb tests/test_client.py
```

### Local Testing

Test the CLI locally:
```bash
python -m s3check --help
python -m s3check --provider aws
```

## Questions?

If you have questions or need help:

- Open an issue on GitHub
- Check existing issues and discussions
- Contact: yduvignau@snapp.fr

Thank you for contributing! 🎉
