"""
UI utilities for s3check.

This module provides color-coded terminal output helpers and formatting utilities
for a consistent and readable user interface.
"""

import sys

# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLOR CODES
# Used throughout for readable, color-coded terminal output.
# ══════════════════════════════════════════════════════════════════════════════

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"

# Global flag to disable colors
_COLORS_ENABLED = True


def disable_colors():
    """
    Disable all ANSI color codes globally.
    
    Useful when redirecting output to a file or running in CI systems
    that don't support ANSI codes.
    """
    global RESET, BOLD, DIM, RED, GREEN, YELLOW, BLUE, CYAN, WHITE, GRAY, _COLORS_ENABLED
    RESET = BOLD = DIM = RED = GREEN = YELLOW = BLUE = CYAN = WHITE = GRAY = ""
    _COLORS_ENABLED = False


def colors_enabled():
    """Check if colors are currently enabled."""
    return _COLORS_ENABLED


# ══════════════════════════════════════════════════════════════════════════════
# PRINT HELPERS
# Thin wrappers around print() for consistent formatting of each log level.
# ══════════════════════════════════════════════════════════════════════════════


def c(color, text):
    """
    Wrap `text` with an ANSI color code and reset at the end.
    
    Args:
        color (str): ANSI color code (e.g., RED, GREEN, BOLD).
        text (str): Text to colorize.
        
    Returns:
        str: Colorized text with reset suffix.
    """
    return f"{color}{text}{RESET}"


def ok(msg):
    """
    Print a success line (green checkmark).
    
    Args:
        msg (str): Success message to display.
    """
    print(f"  {c(GREEN, '✓')} {msg}")


def fail(msg):
    """
    Print a failure line (red cross).
    
    Args:
        msg (str): Error message to display.
    """
    print(f"  {c(RED, '✗')} {msg}")


def warn(msg):
    """
    Print a warning line (yellow exclamation mark).
    
    Args:
        msg (str): Warning message to display.
    """
    print(f"  {c(YELLOW, '!')} {msg}")


def info(msg):
    """
    Print an informational line (blue arrow).
    
    Args:
        msg (str): Informational message to display.
    """
    print(f"  {c(BLUE, '→')} {msg}")


def step(msg):
    """
    Print a section header to visually separate check phases.
    
    Args:
        msg (str): Section title to display.
    """
    print(f"\n{c(BOLD + CYAN, '▸')} {c(BOLD, msg)}")


def prompt_bool(label: str, default: bool = True) -> bool:
    """
    Ask a yes/no question and return a boolean.
    
    The prompt shows "Y/n" when default is True, "y/N" when False.
    Accepts: y, yes, 1, true  →  True
             anything else    →  False (or the default on empty input)
             
    Args:
        label (str): Question to ask the user.
        default (bool): Default value if user presses Enter without typing.
        
    Returns:
        bool: User's response as a boolean.
        
    Examples:
        >>> prompt_bool("Continue?", default=True)
        Continue? (Y/n):
        True
    """
    from s3check.config import prompt
    
    default_str = "Y/n" if default else "y/N"
    val = prompt(label, choices=[default_str])
    if not val:
        return default
    return val.lower() in ("y", "yes", "1", "true")


# ══════════════════════════════════════════════════════════════════════════════
# BANNER
# ASCII art displayed at startup.
# ══════════════════════════════════════════════════════════════════════════════


def banner():
    """Print the tool's ASCII art banner."""
    print(
        c(
            CYAN,
            r"""
 ____  _____        _               _    
/ ___||___ /   ___| |__   ___  ___| | __
\___ \  |_ \  / __| '_ \ / _ \/ __| |/ /
 ___) |___) || (__| | | |  __/ (__|   < 
|____/|____/  \___|_| |_|\___|\___|_|\_\
""",
        )
    )
    print(c(DIM, "  Object Storage Access Verifier\n"))


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY FORMATTING
# Prints a clean, color-coded recap table of all check results.
# ══════════════════════════════════════════════════════════════════════════════


def print_summary(results, provider, cfg):
    """
    Print a formatted summary table after all checks have run.
    
    Status icons:
      ✓ OK      — check passed
      ✗ FAILED  — check failed
      ! DENIED  — access denied (credentials valid, but insufficient permissions)
      - N/A     — check was not attempted (e.g. no bucket specified)
      ? PARTIAL — unexpected / ambiguous result
      
    Args:
        results (dict): Nested dictionary of check results.
        provider (dict): Provider configuration.
        cfg (dict): User configuration.
    """
    print(f"\n{c(BOLD + WHITE, '─' * 52)}")
    print(c(BOLD + WHITE, "  SUMMARY"))
    print(c(BOLD + WHITE, "─" * 52))

    def row(label, status):
        """
        Print a single summary row with a status icon.
        
        Args:
            label (str): Description of the check.
            status: Check result (True/False/"denied"/None/other).
        """
        if status is True:
            icon = c(GREEN, "✓ OK      ")
        elif status is False:
            icon = c(RED, "✗ FAILED  ")
        elif status == "denied":
            icon = c(YELLOW, "! DENIED  ")
        elif status is None:
            icon = c(GRAY, "- N/A     ")
        else:
            icon = c(YELLOW, "? PARTIAL ")
        print(f"  {icon} {label}")

    # Top-level results
    row("boto3 client", results.get("client"))
    row("Authentication", results.get("auth"))

    # Per-bucket results (only shown when a bucket was tested)
    bc = results.get("bucket_checks", {})
    if bc:
        row("Bucket accessible", bc.get("exists"))
        row("List objects (LIST)", bc.get("list"))
        row("Write object (PUT)", bc.get("write"))
        row("Read object (GET)", bc.get("read"))
        row("Delete object (DEL)", bc.get("delete"))

    print()

    # Display measured latency with color coding:
    #   < 200ms → green (good)
    #   < 800ms → yellow (acceptable)
    #   ≥ 800ms → red (slow)
    latency = results.get("latency_ms")
    if latency:
        color = GREEN if latency < 200 else YELLOW if latency < 800 else RED
        print(f"  {c(DIM, 'Latency :')}", c(color, f"{latency}ms"))

    # Determine overall success: all boolean results must be True
    bool_results = [
        v for k, v in results.items() if isinstance(v, bool) and k not in ("buckets",)
    ]
    bc_bools = [v for v in bc.values() if isinstance(v, bool)]
    all_ok = all(bool_results) and (not bc_bools or all(bc_bools))

    print()
    if all_ok:
        print(c(GREEN + BOLD, "  ✓ All checks passed — access is fully operational."))
    else:
        print(c(YELLOW + BOLD, "  ! Some checks failed or were restricted."))
    print()
