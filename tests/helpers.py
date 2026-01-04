"""Shared test utilities for Trifecta integration tests."""

import time
from typing import Callable


def wait_for_condition(
    predicate: Callable[[], bool],
    timeout: float = 5.0,
    poll: float = 0.05,
    description: str = "condition",
) -> bool:
    """Wait for a condition to become true, polling at intervals.

    This helper replaces time.sleep() calls with active polling,
    making tests deterministic and eliminating flaky timeouts.

    Args:
        predicate: A callable that returns True when condition is met.
        timeout: Maximum time to wait in seconds.
        poll: Interval between checks in seconds (small for fast tests).
        description: Human-readable description for error messages.

    Returns:
        True if condition was met, False if timeout expired.

    Example:
        # Instead of: time.sleep(3.5) to wait for TTL expiry
        # Use:
        wait_for_condition(
            lambda: not pid_file.exists(),
            timeout=5.0,
            description="daemon shutdown"
        )
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(poll)
    return False


def wait_for_file(path, timeout: float = 5.0) -> bool:
    """Wait for a file to exist."""
    return wait_for_condition(
        lambda: path.exists(),
        timeout=timeout,
        description=f"file {path} to exist",
    )


def wait_for_file_removal(path, timeout: float = 5.0) -> bool:
    """Wait for a file to be deleted."""
    return wait_for_condition(
        lambda: not path.exists(),
        timeout=timeout,
        description=f"file {path} to be deleted",
    )


def repo_root():
    """Find repository root by searching for pyproject.toml upwards.

    Returns:
        Path: Absolute path to repository root

    Raises:
        FileNotFoundError: If pyproject.toml not found (fail-closed)
    """
    from pathlib import Path

    current = Path(__file__).resolve()

    # Search upwards for pyproject.toml (max 5 levels)
    for _ in range(5):
        current = current.parent
        pyproject = current / "pyproject.toml"

        if pyproject.exists():
            return current

    # Fail-closed: explicit error if not found
    raise FileNotFoundError(
        "Could not find repository root (pyproject.toml). "
        "Ensure tests are running from within the trifecta_dope repository."
    )
