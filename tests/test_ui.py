"""
Tests for s3check.ui module.
"""

import pytest

from s3check.ui import c, colors_enabled, disable_colors


class TestColorFunctions:
    """Tests for color and formatting functions."""

    def test_c_function_with_colors(self):
        """Test that c() wraps text with color codes."""
        from s3check.ui import GREEN, RESET

        result = c(GREEN, "test")
        assert result.startswith(GREEN)
        assert result.endswith(RESET)
        assert "test" in result

    def test_disable_colors(self):
        """Test that disable_colors() removes all color codes."""
        disable_colors()
        assert not colors_enabled()

        # After disabling, c() should return plain text
        result = c("", "test")
        assert result == "test"

    def test_colors_enabled_default(self):
        """Test that colors are enabled by default."""
        # Note: This might fail if run after test_disable_colors
        # In a real test suite, we'd need to reset state or use fixtures
        from s3check import ui

        # Re-import to get fresh state
        import importlib

        importlib.reload(ui)
        assert ui.colors_enabled()


class TestPrintSummary:
    """Tests for print_summary function."""

    def test_print_summary_all_passed(self, capsys):
        """Test summary output when all checks pass."""
        from s3check.ui import print_summary

        results = {
            "client": True,
            "auth": True,
            "latency_ms": 150,
            "bucket_checks": {
                "exists": True,
                "list": True,
                "write": True,
                "read": True,
                "delete": True,
            },
        }
        provider = {"name": "AWS S3"}
        cfg = {"region": "us-east-1"}

        print_summary(results, provider, cfg)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "All checks passed" in captured.out

    def test_print_summary_with_failures(self, capsys):
        """Test summary output when some checks fail."""
        from s3check.ui import print_summary

        results = {
            "client": True,
            "auth": True,
            "latency_ms": 150,
            "bucket_checks": {
                "exists": True,
                "list": True,
                "write": False,
                "read": None,
                "delete": None,
            },
        }
        provider = {"name": "AWS S3"}
        cfg = {"region": "us-east-1"}

        print_summary(results, provider, cfg)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "Some checks failed" in captured.out

    def test_print_summary_without_bucket_checks(self, capsys):
        """Test summary output when no bucket checks were performed."""
        from s3check.ui import print_summary

        results = {
            "client": True,
            "auth": True,
            "latency_ms": 100,
            "buckets": ["bucket1", "bucket2"],
        }
        provider = {"name": "MinIO"}
        cfg = {"endpoint": "http://localhost:9000"}

        print_summary(results, provider, cfg)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "boto3 client" in captured.out
        assert "Authentication" in captured.out
