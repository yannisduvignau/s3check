"""
Tests for s3check.config module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from s3check.config import load_config, validate_config


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_config_valid(self):
        """Test that valid config passes validation."""
        cfg = {"access_key": "AKIAIOSFODNN7EXAMPLE", "secret_key": "wJalrXUtnFEMI"}
        is_valid, error = validate_config(cfg)
        assert is_valid is True
        assert error is None

    def test_validate_config_missing_access_key(self):
        """Test that missing access_key fails validation."""
        cfg = {"secret_key": "wJalrXUtnFEMI"}
        is_valid, error = validate_config(cfg)
        assert is_valid is False
        assert "access_key" in error

    def test_validate_config_missing_secret_key(self):
        """Test that missing secret_key fails validation."""
        cfg = {"access_key": "AKIAIOSFODNN7EXAMPLE"}
        is_valid, error = validate_config(cfg)
        assert is_valid is False
        assert "secret_key" in error

    def test_validate_config_empty_access_key(self):
        """Test that empty access_key fails validation."""
        cfg = {"access_key": "", "secret_key": "wJalrXUtnFEMI"}
        is_valid, error = validate_config(cfg)
        assert is_valid is False

    def test_validate_config_custom_fields(self):
        """Test validation with custom required fields."""
        cfg = {"access_key": "AK123", "region": "us-east-1"}
        is_valid, error = validate_config(cfg, required_fields=["access_key", "region"])
        assert is_valid is True
        assert error is None

    def test_validate_config_custom_fields_missing(self):
        """Test validation with custom required fields missing."""
        cfg = {"access_key": "AK123"}
        is_valid, error = validate_config(cfg, required_fields=["access_key", "region"])
        assert is_valid is False
        assert "region" in error


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_valid_json(self):
        """Test loading a valid JSON config file."""
        config_data = {
            "provider": "AWS S3",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "region": "us-east-1",
            "bucket": "my-bucket",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            cfg = load_config(config_path)
            assert cfg["provider"] == "AWS S3"
            assert cfg["access_key"] == "AKIAIOSFODNN7EXAMPLE"
            assert cfg["region"] == "us-east-1"
            assert cfg["bucket"] == "my-bucket"
        finally:
            Path(config_path).unlink()

    def test_load_config_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/non/existent/file.json")

    def test_load_config_invalid_json(self):
        """Test that loading invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {{{")
            config_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_load_config_preserves_all_fields(self):
        """Test that all fields from config file are preserved."""
        config_data = {
            "provider": "MinIO",
            "access_key": "minioadmin",
            "region": "us-east-1",
            "bucket": "test-bucket",
            "endpoint": "http://localhost:9000",
            "secure": False,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            cfg = load_config(config_path)
            assert cfg == config_data
        finally:
            Path(config_path).unlink()
