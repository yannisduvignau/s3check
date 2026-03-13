"""
Provider definitions for s3check.

This module defines all supported S3-compatible object storage providers
with their specific configuration requirements and endpoint templates.
"""

from typing import Dict, List, Optional

# ══════════════════════════════════════════════════════════════════════════════
# PROVIDER DEFINITIONS
# Each provider entry describes:
#   - name        : Human-readable display name
#   - endpoint    : None (use boto3 default for AWS), "custom" (user-provided),
#                   or a URL template with {placeholders}
#   - fields      : Ordered list of config fields to prompt for in interactive mode
#   - region_default : Pre-filled default region shown in the prompt
# ══════════════════════════════════════════════════════════════════════════════

PROVIDERS = {
    "1": {
        "name": "AWS S3",
        # boto3 resolves the endpoint automatically from the region for AWS,
        # so we don't need to specify one explicitly.
        "endpoint": None,
        "fields": ["access_key", "secret_key", "region", "bucket"],
        "region_default": "us-east-1",
    },
    "2": {
        "name": "MinIO",
        # MinIO is self-hosted, so the endpoint is always a custom URL
        # (e.g. http://localhost:9000 or https://minio.mydomain.com).
        "endpoint": "custom",
        "fields": ["endpoint", "access_key", "secret_key", "bucket", "secure"],
        "region_default": "us-east-1",
    },
    "3": {
        "name": "Cloudflare R2",
        # R2 uses a per-account subdomain. The {account_id} placeholder
        # is replaced at runtime with the value provided by the user.
        "endpoint": "https://{account_id}.r2.cloudflarestorage.com",
        "fields": ["account_id", "access_key", "secret_key", "bucket"],
        "region_default": "auto",
    },
    "4": {
        "name": "DigitalOcean Spaces",
        # Spaces uses a regional endpoint. Common regions: nyc3, ams3, sgp1, sfo3.
        "endpoint": "https://{region}.digitaloceanspaces.com",
        "fields": ["access_key", "secret_key", "region", "bucket"],
        "region_default": "nyc3",
    },
    "5": {
        "name": "Scaleway Object Storage",
        # Scaleway S3-compatible storage. Common regions: fr-par, nl-ams, pl-waw.
        "endpoint": "https://s3.{region}.scw.cloud",
        "fields": ["access_key", "secret_key", "region", "bucket"],
        "region_default": "fr-par",
    },
    "6": {
        "name": "Backblaze B2",
        # Backblaze B2 exposes an S3-compatible API since 2020.
        # Region format example: us-west-004.
        "endpoint": "https://s3.{region}.backblazeb2.com",
        "fields": ["access_key", "secret_key", "region", "bucket"],
        "region_default": "us-west-004",
    },
    "7": {
        "name": "Generic S3-Compatible",
        # Catch-all for any S3-compatible service not listed above
        # (e.g. Ceph, Wasabi, IBM Cloud Object Storage, etc.)
        "endpoint": "custom",
        "fields": ["endpoint", "access_key", "secret_key", "bucket", "region", "secure"],
        "region_default": "us-east-1",
    },
}

# Mapping from CLI short names to provider dictionary keys
PROVIDER_CLI_MAP = {
    "aws": "1",
    "minio": "2",
    "r2": "3",
    "spaces": "4",
    "scaleway": "5",
    "b2": "6",
    "generic": "7",
}


def get_provider(identifier: str) -> Optional[Dict]:
    """
    Get a provider definition by numeric ID or CLI name.
    
    Args:
        identifier (str): Numeric ID (e.g., "1") or CLI name (e.g., "aws").
        
    Returns:
        dict or None: Provider definition, or None if not found.
        
    Examples:
        >>> get_provider("1")
        {'name': 'AWS S3', 'endpoint': None, ...}
        >>> get_provider("aws")
        {'name': 'AWS S3', 'endpoint': None, ...}
    """
    # Try direct numeric lookup first
    if identifier in PROVIDERS:
        return PROVIDERS[identifier]
    
    # Try CLI name mapping
    provider_id = PROVIDER_CLI_MAP.get(identifier.lower())
    if provider_id:
        return PROVIDERS[provider_id]
    
    return None


def get_provider_by_name(name: str) -> Optional[Dict]:
    """
    Get a provider definition by its display name.
    
    Args:
        name (str): Provider display name (e.g., "AWS S3").
        
    Returns:
        dict or None: Provider definition, or None if not found.
    """
    for provider in PROVIDERS.values():
        if provider["name"] == name:
            return provider
    return None


def list_providers() -> List[tuple]:
    """
    Get a list of all providers in display order.
    
    Returns:
        list: List of (id, provider_dict) tuples.
        
    Examples:
        >>> providers = list_providers()
        >>> providers[0]
        ('1', {'name': 'AWS S3', ...})
    """
    return sorted(PROVIDERS.items())


def build_endpoint(provider: Dict, cfg: Dict) -> Optional[str]:
    """
    Resolve the final endpoint URL from the provider definition and user config.
    
    Three cases:
      1. None     → AWS native (boto3 handles it automatically, no endpoint_url)
      2. "custom" → Use the URL typed by the user, adding a scheme if missing
      3. template → Replace {placeholder} tokens with values from `cfg`
      
    Args:
        provider (dict): Provider definition.
        cfg (dict): User configuration with values for placeholders.
        
    Returns:
        str or None: The fully resolved endpoint URL, or None for AWS.
        
    Examples:
        >>> provider = {"endpoint": "https://{region}.example.com"}
        >>> cfg = {"region": "us-west-1"}
        >>> build_endpoint(provider, cfg)
        'https://us-west-1.example.com'
    """
    endpoint = provider["endpoint"]

    # Case 1: AWS S3 — boto3 resolves the endpoint from the region automatically
    if endpoint is None:
        return None

    # Case 2: Custom endpoint (MinIO, generic S3-compatible)
    if endpoint == "custom":
        url = cfg.get("endpoint", "").strip()
        if not url:
            return None
        # Add a scheme if the user omitted it (e.g. "localhost:9000" → "http://…")
        if not url.startswith("http"):
            scheme = "https" if cfg.get("secure", True) else "http"
            url = f"{scheme}://{url}"
        return url

    # Case 3: Template URL — substitute all {key} placeholders from cfg
    for key, val in cfg.items():
        endpoint = endpoint.replace(f"{{{key}}}", str(val))
    return endpoint
