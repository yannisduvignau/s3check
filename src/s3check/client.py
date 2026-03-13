"""
S3 client operations and verification logic for s3check.

This module contains the core logic for running connectivity and permission
checks against S3-compatible object storage providers.
"""

import sys
import time
from typing import Any, Dict

from s3check.providers import build_endpoint
from s3check.ui import BOLD, DIM, GREEN, YELLOW, c, fail, info, ok, step, warn


def run_checks(provider: Dict, cfg: Dict) -> Dict[str, Any]:
    """
    Run all checks against the configured S3-compatible endpoint.
    
    Checks performed (in order):
      1. boto3 client instantiation
      2. list_buckets()  → validates connectivity + authentication
      3. head_bucket()   → checks that the target bucket exists and is reachable
      4. list_objects_v2() → verifies LIST permission on the bucket
      5. put_object()    → verifies WRITE permission (uploads a temporary probe file)
      6. get_object()    → verifies READ permission (downloads the probe file back)
      7. delete_object() → verifies DELETE permission (cleans up the probe file)
      8. get_bucket_location() → retrieves the bucket's region for information
      
    Args:
        provider (dict): The selected provider definition.
        cfg (dict): The user-provided configuration (keys, region, bucket, …).
        
    Returns:
        dict: A nested results dictionary with True/False/"denied"/None per check.
        
    Examples:
        >>> from s3check.providers import get_provider
        >>> provider = get_provider("aws")
        >>> cfg = {"access_key": "AK...", "secret_key": "SK...", "region": "us-east-1"}
        >>> results = run_checks(provider, cfg)
        >>> results["auth"]
        True
    """
    # ── Import boto3 (fail gracefully if not installed) ──────────────────────
    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
    except ImportError:
        print(c(YELLOW + BOLD, "\n  [ERROR] boto3 is not installed."))
        print(c(YELLOW, "  Install it with: pip install boto3\n"))
        sys.exit(1)

    # ── Resolve connection parameters ─────────────────────────────────────────
    endpoint_url = build_endpoint(provider, cfg)
    region = cfg.get("region", "us-east-1") or "us-east-1"
    bucket = cfg.get("bucket", "").strip()

    # Build the kwargs dict passed to boto3.client(). We always set a short
    # timeout to avoid hanging indefinitely on unreachable endpoints.
    boto_kwargs = dict(
        aws_access_key_id=cfg["access_key"],
        aws_secret_access_key=cfg["secret_key"],
        region_name=region,
        config=Config(
            connect_timeout=10,  # seconds to wait for a TCP connection
            read_timeout=10,  # seconds to wait for a response
            retries={"max_attempts": 1},  # no automatic retries — fail fast
        ),
    )

    # For non-AWS providers, we must override the endpoint URL so that boto3
    # does not try to reach s3.amazonaws.com
    if endpoint_url:
        boto_kwargs["endpoint_url"] = endpoint_url

    results = {}  # accumulates all check results

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1 — Client instantiation
    # boto3.client() is synchronous and only validates the parameters locally.
    # It does NOT make any network call at this stage.
    # ─────────────────────────────────────────────────────────────────────────
    step("Initializing S3 client")
    info(f"Provider   : {provider['name']}")
    if endpoint_url:
        info(f"Endpoint   : {endpoint_url}")
    info(f"Region     : {region}")
    if cfg.get("access_key"):
        # Mask most of the access key to avoid leaking it in screenshots/logs
        masked = cfg["access_key"][:6] + "*" * max(0, len(cfg["access_key"]) - 6)
        info(f"Access Key : {masked}")

    try:
        s3 = boto3.client("s3", **boto_kwargs)
        ok("boto3 client created successfully")
        results["client"] = True
    except Exception as e:
        fail(f"Could not create boto3 client: {e}")
        results["client"] = False
        return results  # no point continuing without a client

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2 — Connectivity & authentication
    # list_buckets() is the simplest call that proves both network reachability
    # and valid credentials. We also measure round-trip latency here.
    # ─────────────────────────────────────────────────────────────────────────
    step("Connectivity & authentication")
    t0 = time.time()
    try:
        response = s3.list_buckets()
        latency = int((time.time() - t0) * 1000)  # milliseconds

        buckets = [b["Name"] for b in response.get("Buckets", [])]
        ok(f"Authentication successful ({latency}ms)")
        ok(f"{len(buckets)} bucket(s) visible")
        results["auth"] = True
        results["buckets"] = buckets
        results["latency_ms"] = latency

        # Display a short list of visible buckets (capped at 20 to avoid noise)
        if buckets:
            print(f"\n{c(DIM, '     Buckets found:')}")
            for b in buckets[:20]:
                # Highlight the target bucket (if one was specified) with a star
                marker = c(YELLOW, "★") if (bucket and b == bucket) else c(GREEN, "●")
                print(f"     {marker} {b}")
            if len(buckets) > 20:
                print(c(DIM, f"     … and {len(buckets) - 20} more"))

    except NoCredentialsError:
        # boto3 could not find credentials at all (missing keys)
        fail("Credentials are missing or could not be loaded")
        results["auth"] = False
        return results

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]

        if code in ("InvalidAccessKeyId", "SignatureDoesNotMatch", "AuthFailure", "403"):
            # The server recognized the request but rejected the credentials
            fail(f"Authentication failed: {code} — {msg}")
            results["auth"] = False
            return results

        elif code == "AccessDenied":
            # Credentials are valid but the IAM policy forbids listing all buckets.
            # This is common with scoped service accounts — not necessarily an error.
            warn("Access denied on list_buckets (credentials are valid but scoped)")
            ok("Connectivity confirmed (credentials were accepted by the server)")
            results["auth"] = True
            results["buckets"] = []

        else:
            # Unexpected error — still consider auth as potentially OK
            warn(f"Unexpected error during list_buckets: {code} — {msg}")
            results["auth"] = True
            results["buckets"] = []

    except Exception as e:
        # Network-level error: DNS failure, connection refused, SSL error, etc.
        fail(f"Connection error: {e}")
        results["auth"] = False
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # CHECKS 3–8 — Per-bucket checks (only when a bucket name was provided)
    # ─────────────────────────────────────────────────────────────────────────
    if bucket:
        step(f"Checking bucket: {c(BOLD, bucket)}")
        results["bucket_checks"] = {}

        # ── CHECK 3 — Bucket existence (HEAD bucket) ─────────────────────────
        # head_bucket() returns a 200 if the bucket exists and is accessible,
        # 404 if it doesn't exist, or 403 if access is denied.
        try:
            s3.head_bucket(Bucket=bucket)
            ok("Bucket exists and is accessible")
            results["bucket_checks"]["exists"] = True
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                fail(f"Bucket not found: {bucket}")
            elif code in ("403", "AccessDenied"):
                # The bucket exists (the server would return 404 otherwise),
                # but the caller doesn't have permission to inspect it.
                warn("Bucket exists but access is denied (insufficient permissions)")
                results["bucket_checks"]["exists"] = "denied"
            else:
                fail(f"Unexpected HEAD bucket error: {code}")
            results["bucket_checks"]["exists"] = False

        # ── CHECK 4 — List objects (LIST permission) ──────────────────────────
        # We only request the first 5 keys to keep the response lightweight.
        try:
            resp = s3.list_objects_v2(Bucket=bucket, MaxKeys=5)
            key_count = resp.get("KeyCount", 0)
            ok(f"LIST objects: OK ({key_count} object(s) returned in first page)")
            results["bucket_checks"]["list"] = True

            # Store a few sample keys for display
            sample = [o["Key"] for o in resp.get("Contents", [])]
            results["bucket_checks"]["sample_objects"] = sample
            if sample:
                print(c(DIM, "\n     Sample objects:"))
                for obj in sample:
                    print(c(DIM, f"       · {obj}"))
        except ClientError as e:
            code = e.response["Error"]["Code"]
            fail(f"LIST objects failed: {code}")
            results["bucket_checks"]["list"] = False

        # ── CHECK 5 — Write (PUT object) ──────────────────────────────────────
        # We upload a tiny temporary file to prove write access.
        # The key starts with a dot so it's hidden in most S3 browsers.
        test_key = f".s3check-probe-{int(time.time())}.tmp"
        try:
            s3.put_object(Bucket=bucket, Key=test_key, Body=b"s3check-probe")
            ok(f"PUT object: OK (key: {test_key})")
            results["bucket_checks"]["write"] = True

            # ── CHECK 6 — Read (GET object) ───────────────────────────────────
            # Only attempted if the PUT succeeded, since the object must exist first.
            try:
                obj = s3.get_object(Bucket=bucket, Key=test_key)
                data = obj["Body"].read()
                ok(f"GET object: OK ({len(data)} byte(s) read back)")
                results["bucket_checks"]["read"] = True
            except ClientError as e:
                fail(f"GET object failed: {e.response['Error']['Code']}")
                results["bucket_checks"]["read"] = False

            # ── CHECK 7 — Delete (DELETE object) ──────────────────────────────
            # Always attempt cleanup even if GET failed, to avoid leaving
            # test objects behind in the bucket.
            try:
                s3.delete_object(Bucket=bucket, Key=test_key)
                ok("DELETE object: OK (probe file cleaned up)")
                results["bucket_checks"]["delete"] = True
            except ClientError as e:
                code = e.response["Error"]["Code"]
                warn(f"DELETE object failed: {code} — probe file left behind: {test_key}")
                results["bucket_checks"]["delete"] = False

        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("AccessDenied", "403"):
                warn("PUT object denied — bucket appears to be read-only")
            else:
                fail(f"PUT object failed: {code}")
            # Mark read and delete as N/A since we couldn't create the probe file
            results["bucket_checks"]["write"] = False
            results["bucket_checks"]["read"] = None
            results["bucket_checks"]["delete"] = None

        # ── CHECK 8 — Bucket location (informational only) ───────────────────
        # get_bucket_location() tells us the region the bucket was created in.
        # Useful to catch mismatches between --region and the actual bucket region.
        try:
            loc = s3.get_bucket_location(Bucket=bucket)
            # AWS returns None for us-east-1 (the "null" location constraint)
            location = loc.get("LocationConstraint") or "us-east-1"
            info(f"Bucket region: {location}")
            results["bucket_checks"]["location"] = location
        except ClientError:
            pass  # Non-critical — skip silently if denied or not supported

    return results
