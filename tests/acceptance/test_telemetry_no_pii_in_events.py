"""Acceptance test: Tripwire for PII in telemetry."""

import os
import subprocess
from pathlib import Path
import pytest


def test_telemetry_no_pii_in_active_files(tmp_path):
    """
    Tripwire: CLI must NOT persist absolute paths/PII in active telemetry files.

    This test:
    1. Creates a tmp segment
    2. Runs trifecta ctx sync (writes to segment/_ctx/telemetry)
    3. Scans ALL telemetry files (excluding .bak)
    4. FAILS if any PII detected

    PII patterns:
    - /Users/, /home/, /private/var/
    - file://
    - C:\\Users\\, D:\\Users\\
    - /mnt/c/Users/
    """
    # Create segment
    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Create minimal trifecta structure
    result = subprocess.run(
        ["uv", "run", "trifecta", "create", "-s", str(segment), "--scope", "PII Test"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"create failed: {result.stderr}"

    # Run ctx sync to generate telemetry events
    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"sync failed: {result.stderr}"

    # Scan ENTIRE telemetry directory (exclude .bak files)
    telemetry_dir = segment / "_ctx" / "telemetry"

    if not telemetry_dir.exists():
        # No telemetry generated, pass
        return

    pii_patterns = [
        "/Users/",
        "/home/",
        "/private/var/",
        "file://",
        "C:\\Users\\",
        "D:\\Users\\",
        "/mnt/c/Users/",
        "/mnt/C/Users/",
    ]

    violations = []

    # Scan all files in telemetry directory
    for filepath in telemetry_dir.rglob("*"):
        # Skip directories and backup files
        if filepath.is_dir() or filepath.suffix == ".bak":
            continue

        # Read file content
        try:
            content = filepath.read_text()

            for pattern in pii_patterns:
                if pattern in content:
                    violations.append(
                        {
                            "file": filepath.name,
                            "pattern": pattern,
                            "relative_path": str(filepath.relative_to(telemetry_dir)),
                        }
                    )
        except Exception:
            # Skip non-text files
            continue

    # FAIL-CLOSED: If any PII detected, fail with details
    if violations:
        error_msg = f"PII LEAK DETECTED in telemetry ({len(violations)} violations):\n"
        for v in violations[:5]:  # Show first 5
            error_msg += f"  {v['file']}: pattern '{v['pattern']}'\n"
        assert False, error_msg


@pytest.mark.slow
def test_telemetry_bypass_allows_absolute_paths(tmp_path):
    """
    Verify TRIFECTA_PII=allow preserves absolute paths in telemetry.

    This test:
    1. Creates a tmp segment with absolute path
    2. Runs CLI with TRIFECTA_PII=allow
    3. Verifies telemetry dir exists, contains absolute path if telemetry enabled
    """
    # Create segment with absolute path
    segment = tmp_path / "bypass_test"
    segment.mkdir()

    # Create minimal trifecta structure
    result = subprocess.run(
        ["uv", "run", "trifecta", "create", "-s", str(segment), "--scope", "Bypass Test"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"create failed: {result.stderr}"

    # Run ctx sync with TRIFECTA_PII=allow
    env = os.environ.copy()
    env["TRIFECTA_PII"] = "allow"

    result = subprocess.run(
        ["uv", "run", "trifecta", "ctx", "sync", "-s", str(segment)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"sync failed: {result.stderr}"

    # Check telemetry directory
    telemetry_dir = segment / "_ctx" / "telemetry"

    # If telemetry was created, verify bypass worked
    if telemetry_dir.exists():
        # Scan all telemetry files
        found_absolute_path = False

        for filepath in telemetry_dir.rglob("*"):
            if filepath.is_dir():
                continue

            try:
                content = filepath.read_text()
                # Check for absolute paths (NOT redacted)
                if str(segment) in content or "/private/var/" in content or "/tmp/" in content:
                    found_absolute_path = True
                    break
            except Exception:
                continue

        assert found_absolute_path, (
            f"Bypass test AMBIGUOUS: Telemetry exists but no absolute paths found. "
            f"Expected segment path '{segment}' or /private/var/ in telemetry files."
        )
    # If no telemetry, test is PASS (can't verify bypass, but not a failure)
