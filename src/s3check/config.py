"""
Configuration management for s3check.

This module handles interactive prompts, config file loading/saving,
and configuration validation.
"""

import getpass
import json
import sys
import time
from typing import Dict, Optional

from s3check.providers import PROVIDERS, build_endpoint
from s3check.ui import BOLD, DIM, RED, WHITE, YELLOW, c, info, ok, prompt_bool


def prompt(
    label: str,
    default: Optional[str] = None,
    secret: bool = False,
    choices: Optional[list] = None,
) -> str:
    """
    Display a styled prompt and return the user's input.

    Args:
        label (str): The field name shown to the user.
        default (str, optional): Pre-filled value shown in brackets; used if user presses Enter.
        secret (bool): If True, use getpass so the input is not echoed to the terminal.
        choices (list, optional): Optional list of accepted values shown as a hint.

    Returns:
        str: The user's input string, or `default` if the input is empty.

    Examples:
        >>> prompt("Region", default="us-east-1")
        'us-east-1'
        >>> prompt("Secret Key", secret=True)
        # (hidden input)
    """
    # Build the suffix shown after the label (e.g. " [us-east-1]" or " (Y/n)")
    suffix = f" [{c(DIM, default)}]" if default else ""
    if choices:
        suffix += f" ({'/'.join(choices)})"

    display = f"  {c(BOLD + WHITE, label)}{suffix}: "

    try:
        if secret:
            # getpass hides the input — important for secret keys
            val = getpass.getpass(display)
        else:
            val = input(display).strip()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or piped EOF: exit gracefully
        print()
        sys.exit(0)

    # Fall back to the default when the user presses Enter without typing
    if not val and default is not None:
        val = default

    return val


def select_provider() -> Dict:
    """
    Display the numbered provider menu and return the chosen provider dict.

    Loops until a valid number is entered.

    Returns:
        dict: Selected provider configuration.
    """
    print(c(BOLD + WHITE, "\n  Select your provider:\n"))
    for k, v in PROVIDERS.items():
        print(f"    {c(DIM, k)}) {v['name']}")
    print()

    while True:
        choice = prompt("Provider", default="1")
        if choice in PROVIDERS:
            return PROVIDERS[choice]
        print(c(RED, "  Invalid choice, please enter a number from the list."))


def collect_config(provider: Dict) -> Dict:
    """
    Prompt the user for each field required by the given provider.

    The `fields` list on the provider determines both the order and the
    set of prompts displayed. Only fields declared in that list are asked.

    Args:
        provider (dict): Provider definition.

    Returns:
        dict: A flat config dictionary (access_key, secret_key, region, …).
    """
    cfg = {}
    fields = provider["fields"]
    print()  # blank line for visual spacing

    for field in fields:
        if field == "access_key":
            # The access key ID is not sensitive, so we show it in clear text
            cfg["access_key"] = prompt("Access Key ID")

        elif field == "secret_key":
            # The secret key must never be echoed — use getpass
            cfg["secret_key"] = prompt("Secret Access Key", secret=True)

        elif field == "region":
            # Region is pre-filled with the provider's sensible default
            cfg["region"] = prompt("Region", default=provider["region_default"])

        elif field == "bucket":
            # Bucket is optional: leaving it empty skips per-bucket checks
            cfg["bucket"] = prompt(
                "Bucket name (optional — leave empty to only list buckets)", default=""
            )

        elif field == "endpoint":
            # For custom/self-hosted providers, the full URL is required
            cfg["endpoint"] = prompt("Endpoint URL (e.g. http://localhost:9000)")

        elif field == "account_id":
            # Cloudflare R2 needs the account ID to build the endpoint URL
            cfg["account_id"] = prompt("Cloudflare Account ID")

        elif field == "secure":
            # Whether to use HTTPS or plain HTTP (relevant for local MinIO)
            cfg["secure"] = prompt_bool("Use HTTPS (TLS)", default=True)

    return cfg


def save_config(provider: Dict, cfg: Dict, interactive: bool = True) -> Optional[str]:
    """
    Save the current config (without the secret key) to a JSON file.

    The saved file can be reloaded with --config on subsequent runs.
    The secret key must always be re-entered or provided via environment variable.

    Args:
        provider (dict): Provider configuration.
        cfg (dict): User configuration.
        interactive (bool): If True, prompt user before saving.

    Returns:
        str or None: Filename if saved, None otherwise.
    """
    if interactive:
        print(c(DIM, "─" * 52))
        if not prompt_bool("Save config for future use? (secret key excluded)", default=False):
            return None

    # Strip the secret key before writing to disk
    safe_cfg = {k: v for k, v in cfg.items() if k != "secret_key"}
    safe_cfg["provider"] = provider["name"]

    fname = f"s3check_{provider['name'].replace(' ', '_').lower()}_{int(time.time())}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(safe_cfg, f, indent=2)

    ok(f"Config saved to: {fname}")
    info("Re-run with: python -m s3check --config " + fname)
    return fname


def load_config(path: str) -> Dict:
    """
    Load a previously saved JSON config file.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict: The parsed config dictionary.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        json.JSONDecodeError: If the config file is not valid JSON.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_config(cfg: Dict, required_fields: Optional[list] = None) -> tuple:
    """
    Validate a configuration dictionary.

    Args:
        cfg (dict): Configuration to validate.
        required_fields (list, optional): List of required field names.

    Returns:
        tuple: (is_valid: bool, error_message: str or None)

    Examples:
        >>> validate_config({"access_key": "AK123", "secret_key": "SK456"})
        (True, None)
        >>> validate_config({"access_key": "AK123"}, ["access_key", "secret_key"])
        (False, "Missing required field: secret_key")
    """
    if required_fields is None:
        required_fields = ["access_key", "secret_key"]

    for field in required_fields:
        if not cfg.get(field):
            return False, f"Missing required field: {field}"

    return True, None
