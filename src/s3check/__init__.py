"""
s3check — Object Storage Access Verifier
=========================================

A lightweight console tool to verify connectivity and permissions against any
S3-compatible object storage provider.

Supported providers:
- AWS S3
- MinIO
- Cloudflare R2
- DigitalOcean Spaces
- Scaleway Object Storage
- Backblaze B2
- Generic S3-Compatible services

Example:
    >>> from s3check import verify
    >>> results = verify(provider="aws", access_key="...", secret_key="...", bucket="my-bucket")
    >>> print(results["auth"])  # True if authenticated
"""

__version__ = "1.0.0"
__author__ = "Yannis Duvignau"
__email__ = "yduvignau@snapp.fr"
__license__ = "MIT"

from s3check.client import run_checks as verify

__all__ = ["verify", "__version__"]
