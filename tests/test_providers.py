"""
Tests for s3check.providers module.
"""

import pytest

from s3check.providers import (
    PROVIDERS,
    PROVIDER_CLI_MAP,
    build_endpoint,
    get_provider,
    get_provider_by_name,
    list_providers,
)


class TestGetProvider:
    """Tests for get_provider function."""

    def test_get_provider_by_numeric_id(self):
        """Test retrieving provider by numeric ID."""
        provider = get_provider("1")
        assert provider is not None
        assert provider["name"] == "AWS S3"
        assert provider["endpoint"] is None

    def test_get_provider_by_cli_name(self):
        """Test retrieving provider by CLI name."""
        provider = get_provider("aws")
        assert provider is not None
        assert provider["name"] == "AWS S3"

    def test_get_provider_invalid(self):
        """Test that invalid provider returns None."""
        provider = get_provider("invalid")
        assert provider is None

    def test_get_all_providers(self):
        """Test that all providers can be retrieved."""
        for cli_name, provider_id in PROVIDER_CLI_MAP.items():
            provider = get_provider(cli_name)
            assert provider is not None
            assert provider == PROVIDERS[provider_id]


class TestGetProviderByName:
    """Tests for get_provider_by_name function."""

    def test_get_provider_by_exact_name(self):
        """Test retrieving provider by exact display name."""
        provider = get_provider_by_name("AWS S3")
        assert provider is not None
        assert provider["name"] == "AWS S3"

    def test_get_provider_by_name_not_found(self):
        """Test that non-existent provider name returns None."""
        provider = get_provider_by_name("Non-Existent Provider")
        assert provider is None


class TestListProviders:
    """Tests for list_providers function."""

    def test_list_providers_returns_tuples(self):
        """Test that list_providers returns list of tuples."""
        providers = list_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0
        assert all(isinstance(p, tuple) for p in providers)

    def test_list_providers_contains_all(self):
        """Test that list_providers contains all defined providers."""
        providers = list_providers()
        assert len(providers) == len(PROVIDERS)


class TestBuildEndpoint:
    """Tests for build_endpoint function."""

    def test_build_endpoint_aws(self):
        """Test that AWS provider returns None (boto3 handles it)."""
        provider = {"endpoint": None}
        cfg = {"region": "us-east-1"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint is None

    def test_build_endpoint_custom_with_scheme(self):
        """Test custom endpoint with explicit scheme."""
        provider = {"endpoint": "custom"}
        cfg = {"endpoint": "https://minio.example.com:9000"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://minio.example.com:9000"

    def test_build_endpoint_custom_without_scheme_secure(self):
        """Test custom endpoint without scheme defaults to https."""
        provider = {"endpoint": "custom"}
        cfg = {"endpoint": "minio.example.com:9000", "secure": True}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://minio.example.com:9000"

    def test_build_endpoint_custom_without_scheme_insecure(self):
        """Test custom endpoint without scheme uses http when secure=False."""
        provider = {"endpoint": "custom"}
        cfg = {"endpoint": "localhost:9000", "secure": False}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "http://localhost:9000"

    def test_build_endpoint_template_with_region(self):
        """Test endpoint template with region placeholder."""
        provider = {"endpoint": "https://s3.{region}.example.com"}
        cfg = {"region": "eu-west-1"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://s3.eu-west-1.example.com"

    def test_build_endpoint_template_with_multiple_placeholders(self):
        """Test endpoint template with multiple placeholders."""
        provider = {"endpoint": "https://{account_id}.{region}.example.com"}
        cfg = {"account_id": "abc123", "region": "us-east-1"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://abc123.us-east-1.example.com"

    def test_build_endpoint_custom_empty(self):
        """Test custom endpoint with empty value returns None."""
        provider = {"endpoint": "custom"}
        cfg = {"endpoint": ""}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint is None

    def test_build_endpoint_cloudflare_r2(self):
        """Test Cloudflare R2 endpoint building."""
        provider = PROVIDERS["3"]  # Cloudflare R2
        cfg = {"account_id": "abc123"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://abc123.r2.cloudflarestorage.com"

    def test_build_endpoint_digitalocean_spaces(self):
        """Test DigitalOcean Spaces endpoint building."""
        provider = PROVIDERS["4"]  # DigitalOcean Spaces
        cfg = {"region": "nyc3"}
        endpoint = build_endpoint(provider, cfg)
        assert endpoint == "https://nyc3.digitaloceanspaces.com"
