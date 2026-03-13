# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-13

### Added
- Complete refactoring to professional package structure
- Modern Python packaging with `pyproject.toml`
- Modular architecture with separate modules:
  - `cli.py` - Command-line interface
  - `client.py` - S3 client and verification logic
  - `config.py` - Configuration management
  - `providers.py` - Provider definitions
  - `ui.py` - Terminal UI utilities
- Comprehensive test suite with pytest
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Type hints throughout codebase
- Detailed docstrings following Google style
- Makefile for common development tasks
- Docker support with multi-stage builds
- Example configurations for AWS and MinIO
- CONTRIBUTING.md with contributor guidelines
- MIT License
- Professional README with badges and comprehensive documentation

### Changed
- Migrated from single `main.py` to modular package structure
- Improved code organization and maintainability
- Enhanced error handling and user feedback
- Better separation of concerns

### Fixed
- Code style consistency with black and isort
- Type checking with mypy
- Security scans with bandit

## [0.1.0] - Previous Version

### Added
- Initial release as single-file script
- Support for AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces, Scaleway, Backblaze B2
- Interactive mode with guided prompts
- CLI mode with command-line flags
- Config file support (secret key excluded)
- Environment variable support
- Color-coded terminal output
- Comprehensive S3 permission checks (LIST, READ, WRITE, DELETE)
- Latency measurement
- Bucket listing with target highlighting
