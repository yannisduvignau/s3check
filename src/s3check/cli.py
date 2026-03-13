#!/usr/bin/env python3
"""
CLI entry point for s3check.

This module handles command-line argument parsing and orchestrates the
interactive/non-interactive modes.
"""

import argparse
import getpass
import os
import sys

from s3check import __version__
from s3check.client import run_checks
from s3check.config import collect_config, load_config, save_config, select_provider
from s3check.providers import PROVIDER_CLI_MAP, PROVIDERS, get_provider_by_name
from s3check.ui import BOLD, DIM, WHITE, YELLOW, banner, c, disable_colors, print_summary


def main():
    """
    Main entry point for the s3check CLI application.

    Handles three modes:
      1. Non-interactive CLI mode  (--provider / --access-key / … flags)
      2. Config file mode          (--config flag)
      3. Interactive guided mode   (default, no flags)
    """
    parser = argparse.ArgumentParser(
        prog="s3check",
        description="s3check — Object Storage Access Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  s3check
  s3check --config saved_config.json
  s3check --provider aws --access-key AKID --secret-key SECRET --region eu-west-1 --bucket my-bucket
  s3check --provider minio --endpoint http://localhost:9000 --access-key admin --secret-key password
  s3check --provider r2 --access-key KEY --secret-key SECRET --bucket my-bucket

environment variables:
  AWS_ACCESS_KEY_ID      Used as access key if --access-key is not provided
  AWS_SECRET_ACCESS_KEY  Used as secret key if --secret-key is not provided
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config", metavar="FILE", help="Path to a previously saved JSON config file"
    )
    parser.add_argument(
        "--provider",
        choices=["aws", "minio", "r2", "spaces", "scaleway", "b2", "generic"],
        help="Storage provider (skips the interactive provider menu)",
    )
    parser.add_argument("--access-key", metavar="KEY", help="Access key ID")
    parser.add_argument("--secret-key", metavar="SECRET", help="Secret access key")
    parser.add_argument("--region", metavar="REGION", help="AWS region (e.g. eu-west-1)")
    parser.add_argument(
        "--bucket", metavar="BUCKET", help="Bucket name to run per-bucket checks on"
    )
    parser.add_argument(
        "--endpoint",
        metavar="URL",
        help="Custom endpoint URL (for MinIO, generic S3)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output (useful when redirecting to a file or CI logs)",
    )

    args = parser.parse_args()

    # ── Disable colors if requested ───────────────────────────────────────────
    if args.no_color:
        disable_colors()

    banner()

    # ── Mode 1: Non-interactive — provider passed via CLI flag ────────────────
    if args.provider:
        provider_id = PROVIDER_CLI_MAP[args.provider]
        provider = PROVIDERS[provider_id]

        # Build config from CLI args, falling back to environment variables
        cfg = {
            "access_key": args.access_key or os.environ.get("AWS_ACCESS_KEY_ID", ""),
            "secret_key": args.secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            "region": args.region or provider["region_default"],
            "bucket": args.bucket or "",
            "endpoint": args.endpoint or "",
        }

        # Validate that required credentials are present
        if not cfg["access_key"] or not cfg["secret_key"]:
            print(
                c(
                    YELLOW + BOLD,
                    "\n  [ERROR] Missing credentials. Provide them via CLI flags "
                    "or environment variables.\n",
                )
            )
            print(c(DIM, "  CLI flags:"))
            print(c(DIM, "    --access-key <key>"))
            print(c(DIM, "    --secret-key <secret>"))
            print()
            print(c(DIM, "  Environment variables:"))
            print(c(DIM, "    AWS_ACCESS_KEY_ID=<key>"))
            print(c(DIM, "    AWS_SECRET_ACCESS_KEY=<secret>"))
            print()
            sys.exit(1)

    # ── Mode 2: Config file — load from a previously saved JSON ───────────────
    elif args.config:
        try:
            raw = load_config(args.config)
        except FileNotFoundError:
            print(c(YELLOW + BOLD, f"\n  [ERROR] Config file not found: {args.config}\n"))
            sys.exit(1)
        except Exception as e:
            print(c(YELLOW + BOLD, f"\n  [ERROR] Failed to load config: {e}\n"))
            sys.exit(1)

        # Find the matching provider by name, defaulting to "Generic S3-Compatible"
        pname = raw.pop("provider", "")
        provider = get_provider_by_name(pname)
        if not provider:
            print(
                c(
                    YELLOW + BOLD,
                    f"\n  [WARNING] Unknown provider '{pname}' in config, "
                    f"using Generic S3-Compatible\n",
                )
            )
            provider = PROVIDERS["7"]

        # Secret key is never stored in the config file.
        # Try the environment variable first, then prompt interactively.
        raw.setdefault("secret_key", os.environ.get("AWS_SECRET_ACCESS_KEY", ""))
        if not raw["secret_key"]:
            raw["secret_key"] = getpass.getpass(
                f"  {c(BOLD + WHITE, 'Secret Access Key')}: "
            ).strip()

        cfg = raw

    # ── Mode 3: Interactive — guided step-by-step prompts ─────────────────────
    else:
        provider = select_provider()
        cfg = collect_config(provider)

    # ── Run all checks ────────────────────────────────────────────────────────
    try:
        results = run_checks(provider, cfg)
    except KeyboardInterrupt:
        print(c(YELLOW, "\n\n  Interrupted."))
        sys.exit(0)

    # ── Print the summary table ───────────────────────────────────────────────
    print_summary(results, provider, cfg)

    # ── Offer to save config (interactive mode only) ──────────────────────────
    # We skip this in CLI/config-file mode since the user is likely scripting.
    if not args.provider and not args.config:
        save_config(provider, cfg, interactive=True)


if __name__ == "__main__":
    main()
