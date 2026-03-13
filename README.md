# s3check — Object Storage Access Verifier

[![CI](https://github.com/yannisduvignau/s3check/workflows/CI/badge.svg)](https://github.com/yannisduvignau/s3check/actions)
[![codecov](https://codecov.io/gh/yannisduvignau/s3check/branch/main/graph/badge.svg)](https://codecov.io/gh/yannisduvignau/s3check)
[![PyPI version](https://badge.fury.io/py/s3check.svg)](https://badge.fury.io/py/s3check)
[![Python versions](https://img.shields.io/pypi/pyversions/s3check.svg)](https://pypi.org/project/s3check/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A lightweight, professional-grade console tool to verify connectivity and permissions against any S3-compatible object storage provider.

```
 ____  _____        _               _    
/ ___||___ /   ___| |__   ___  ___| | __
\___ \  |_ \  / __| '_ \ / _ \/ __| |/ /
 ___) |___) || (__| | | |  __/ (__|   < 
|____/|____/  \___|_| |_|\___|\___|_|\_\
```

---

## ✨ Features

- 🔌 **Multi-Provider Support** — Works with AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces, Scaleway, Backblaze B2, and any S3-compatible service
- 🔐 **Comprehensive Permission Testing** — Validates READ, WRITE, LIST, and DELETE permissions
- ⚡ **Fast & Lightweight** — Minimal dependencies, quick checks with latency measurement
- 🎨 **Beautiful CLI** — Color-coded output with clear status indicators
- 📝 **Config File Support** — Save and reuse configurations (secrets excluded)
- 🔒 **Security First** — Never stores secret keys, masked credential display
- 🐍 **Modern Python** — Type hints, modular architecture, comprehensive tests
- 🚀 **CI/CD Ready** — Perfect for automation and integration testing

---

## 📋 Supported Providers

| # | Provider | Default Region | Endpoint Type |
|---|----------|----------------|---------------|
| 1 | **AWS S3** | `us-east-1` | Auto-configured |
| 2 | **MinIO** | `us-east-1` | Custom URL |
| 3 | **Cloudflare R2** | `auto` | Account-based |
| 4 | **DigitalOcean Spaces** | `nyc3` | Regional |
| 5 | **Scaleway Object Storage** | `fr-par` | Regional |
| 6 | **Backblaze B2** | `us-west-004` | Regional |
| 7 | **Generic S3-Compatible** | `us-east-1` | Custom URL |

---

## 🚀 Installation

### From PyPI (Recommended)

```bash
pip install s3check
```

### From Source

```bash
git clone https://github.com/yannisduvignau/s3check.git
cd s3check
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/yannisduvignau/s3check.git
cd s3check
make install-dev
# or
pip install -e ".[dev]"
```

---

## 📖 Usage

### Interactive Mode (Default)

The easiest way to use s3check — just run it and follow the prompts:

```bash
s3check
```

### Non-Interactive CLI Mode

Perfect for scripting and CI/CD pipelines:

```bash
# AWS S3
s3check --provider aws \
  --access-key AKIAIOSFODNN7EXAMPLE \
  --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --region eu-west-1 \
  --bucket my-bucket

# MinIO (local)
s3check --provider minio \
  --endpoint http://localhost:9000 \
  --access-key minioadmin \
  --secret-key minioadmin \
  --bucket my-bucket

# Cloudflare R2
s3check --provider r2 \
  --access-key <R2_ACCESS_KEY> \
  --secret-key <R2_SECRET_KEY> \
  --bucket my-bucket

# DigitalOcean Spaces
s3check --provider spaces \
  --access-key <SPACES_KEY> \
  --secret-key <SPACES_SECRET> \
  --region nyc3 \
  --bucket my-bucket
```

### Config File Mode

Save time by reusing configurations:

```bash
# Load a previously saved config
s3check --config my-config.json

# Or set the secret key via environment variable
export AWS_SECRET_ACCESS_KEY=mysecret
s3check --config my-config.json
```

Example config files are available in the [`examples/`](examples/) directory.

### Environment Variables

Automatically read if CLI flags are not provided:

| Variable | Used For |
|----------|----------|
| `AWS_ACCESS_KEY_ID` | Access key |
| `AWS_SECRET_ACCESS_KEY` | Secret key |

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

s3check --provider aws --region eu-west-1 --bucket my-bucket
```

### Disable Colors

For CI systems or log files:

```bash
s3check --no-color
```

---

## 🔍 What It Checks

For each run, s3check performs up to **8 sequential checks**:

| Step | API Call | What it validates |
|------|----------|-------------------|
| 1 | — | boto3 client creation with provided credentials |
| 2 | `list_buckets` | Network connectivity + authentication |
| 3 | `head_bucket` | Target bucket exists and is reachable |
| 4 | `list_objects_v2` | LIST permission on the bucket |
| 5 | `put_object` | WRITE permission (uploads a temporary probe file) |
| 6 | `get_object` | READ permission (downloads the probe file back) |
| 7 | `delete_object` | DELETE permission (cleans up the probe file) |
| 8 | `get_bucket_location` | Informational — bucket region |

**Notes:**
- Steps 3–8 only run when a **bucket name** is provided
- Steps 6 and 7 only run if step 5 (PUT) succeeded
- The probe file (`.s3check-probe-<timestamp>.tmp`) is automatically cleaned up

---

## 📊 Example Output

```
 ▸ Initializing S3 client
   → Provider   : AWS S3
   → Region     : eu-west-1
   → Access Key : AKIAXXX******
   ✓ boto3 client created successfully

 ▸ Connectivity & authentication
   ✓ Authentication successful (142ms)
   ✓ 3 bucket(s) visible

      Buckets found:
      ● my-bucket
      ● my-other-bucket
      ★ my-target-bucket     ← target bucket

 ▸ Checking bucket: my-target-bucket
   ✓ Bucket exists and is accessible
   ✓ LIST objects: OK (5 object(s) returned in first page)
   ✓ PUT object: OK (key: .s3check-probe-1234567890.tmp)
   ✓ GET object: OK (13 byte(s) read back)
   ✓ DELETE object: OK (probe file cleaned up)
   → Bucket region: eu-west-1

────────────────────────────────────────────────────
  SUMMARY
────────────────────────────────────────────────────
  ✓ OK       boto3 client
  ✓ OK       Authentication
  ✓ OK       Bucket accessible
  ✓ OK       List objects (LIST)
  ✓ OK       Write object (PUT)
  ✓ OK       Read object (GET)
  ✓ OK       Delete object (DEL)

  Latency : 142ms

  ✓ All checks passed — access is fully operational.
```

---

## 🛠️ Development

### Project Structure

```
object-storage-access-verifier/
├── src/s3check/           # Source code
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # CLI entry point
│   ├── client.py         # S3 client and checks logic
│   ├── config.py         # Configuration management
│   ├── providers.py      # Provider definitions
│   └── ui.py             # Terminal UI utilities
├── tests/                # Test suite
│   ├── test_providers.py
│   ├── test_config.py
│   └── test_ui.py
├── examples/             # Example configurations
├── .github/workflows/    # CI/CD pipelines
├── pyproject.toml        # Modern Python packaging
├── Makefile              # Common tasks
└── README.md             # This file
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_providers.py

# Run specific test
pytest tests/test_providers.py::TestBuildEndpoint::test_build_endpoint_aws
```

### Code Quality

```bash
# Format code
make format

# Check formatting
make format-check

# Run linters
make lint

# Run all quality checks
make format lint test
```

### Building

```bash
# Build distribution packages
make build

# Publish to PyPI (requires credentials)
make publish
```

---

## 🐳 Docker

Build and run s3check in a container:

```bash
# Build image
make docker-build

# Run interactively
make docker-run

# Or use docker directly
docker build -t s3check .
docker run -it --rm \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  s3check --provider aws --region us-east-1
```

---

## 🤝 Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

---

## 📝 CLI Reference

```
usage: s3check [-h] [--version] [--config FILE] 
               [--provider {aws,minio,r2,spaces,scaleway,b2,generic}]
               [--access-key KEY] [--secret-key SECRET] [--region REGION]
               [--bucket BUCKET] [--endpoint URL] [--no-color]

optional arguments:
  --version             Show program's version number and exit
  --config FILE         Path to a previously saved JSON config file
  --provider PROVIDER   Storage provider (skips the interactive menu)
  --access-key KEY      Access key ID
  --secret-key SECRET   Secret access key
  --region REGION       AWS region (e.g. eu-west-1)
  --bucket BUCKET       Bucket name to run per-bucket checks on
  --endpoint URL        Custom endpoint URL (for MinIO, generic S3)
  --no-color            Disable ANSI color output
```

---

## 📚 Python API

Use s3check programmatically in your Python code:

```python
from s3check import verify
from s3check.providers import get_provider

# Get provider configuration
provider = get_provider("aws")

# Run checks
results = verify(
    provider=provider,
    cfg={
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/...",
        "region": "us-east-1",
        "bucket": "my-bucket"
    }
)

# Check results
if results["auth"]:
    print("✓ Authentication successful")
    print(f"Latency: {results['latency_ms']}ms")

if results.get("bucket_checks", {}).get("write"):
    print("✓ Write permission confirmed")
```

---

## ⚠️ Security Notes

- **Secret keys are NEVER written to disk** — Config files exclude them by default
- Credentials are **masked in output** (only first 6 chars shown)
- The **probe file** (`.s3check-probe-*.tmp`) is automatically deleted
- For scoped IAM policies, `list_buckets` may fail — this is expected behavior

---

## 📄 License

This project is licensed under the MIT License - see the [`LICENSE`](LICENSE) file for details.

---

## 👤 Author

**Yannis Duvignau**
- Email: yduvignau@snapp.fr
- GitHub: [@yannisduvignau](https://github.com/yannisduvignau)

---

## 🙏 Acknowledgments

- Built with [boto3](https://boto3.amazonaws.com/) — the AWS SDK for Python
- Inspired by the need for a quick, reliable S3 connectivity tester
- Thanks to all contributors who help improve this tool

---

## 📈 Roadmap

- [ ] Add support for more S3-compatible providers
- [ ] Implement parallel bucket checks
- [ ] Add JSON output mode for programmatic parsing
- [ ] Create GitHub Action for CI/CD integration
- [ ] Add Docker image to Docker Hub
- [ ] Support for testing with temporary credentials (STS)

---

<div align="center">
  <strong>Made with ❤️ for DevOps engineers and cloud practitioners</strong>
</div>
