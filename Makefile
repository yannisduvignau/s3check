.PHONY: help install install-dev test lint format clean build publish run

# Default target
help:
	@echo "s3check - Object Storage Access Verifier"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        Install the package in production mode"
	@echo "  make install-dev    Install the package with development dependencies"
	@echo "  make test           Run tests with pytest"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make lint           Run code quality checks (flake8, mypy)"
	@echo "  make format         Auto-format code with black and isort"
	@echo "  make format-check   Check code formatting without modifying"
	@echo "  make clean          Remove build artifacts and caches"
	@echo "  make build          Build distribution packages"
	@echo "  make publish        Publish to PyPI (requires credentials)"
	@echo "  make publish-test   Publish to TestPyPI"
	@echo "  make run            Run s3check in interactive mode"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run s3check in Docker container"

# Install package in production mode
install:
	pip install -e .

# Install package with development dependencies
install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Run tests
test:
	pytest

# Run tests with coverage report
test-cov:
	pytest --cov=s3check --cov-report=html --cov-report=term

# Run linting and type checking
lint:
	@echo "Running flake8..."
	flake8 src/s3check tests
	@echo "Running mypy..."
	mypy src/s3check

# Auto-format code
format:
	@echo "Running isort..."
	isort src/s3check tests
	@echo "Running black..."
	black src/s3check tests

# Check formatting without modifying
format-check:
	@echo "Checking isort..."
	isort --check-only src/s3check tests
	@echo "Checking black..."
	black --check src/s3check tests

# Clean build artifacts and cache
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Build distribution packages
build: clean
	python -m build

# Publish to PyPI
publish: build
	python -m twine upload dist/*

# Publish to TestPyPI
publish-test: build
	python -m twine upload --repository testpypi dist/*

# Run s3check in interactive mode
run:
	python -m s3check

# Run s3check with AWS example
run-aws:
	python -m s3check --provider aws --region us-east-1

# Docker targets
docker-build:
	docker build -t s3check:latest .

docker-run:
	docker run -it --rm s3check:latest

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files
