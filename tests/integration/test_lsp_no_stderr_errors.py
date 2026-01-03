"""
Tripwire test: Ensure LSP client lifecycle doesn't produce stderr errors.

This test monitors stderr/stdout during LSP daemon tests to ensure
no "LSP Loop Exception" or "write to closed file" messages appear.
"""

import subprocess
import sys


def test_no_lsp_loop_exceptions():
    """Tripwire: LSP tests must not print forbidden error messages."""
    # Run the LSP tests and capture all output
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/integration/test_lsp_daemon.py",
            "tests/integration/test_lsp_telemetry.py",
        ],
        cwd=".",
        capture_output=True,
        text=True,
    )

    combined_output = result.stdout + result.stderr

    # Gate: LSP tests must have actually run (prevent false PASS)
    assert result.returncode == 0, (
        f"LSP tests failed with exit code {result.returncode}. "
        f"This tripwire requires passing tests to be meaningful."
    )
    assert "passed" in combined_output.lower(), (
        "No test execution detected in output. Tripwire may not be testing anything."
    )

    # Check for forbidden strings
    forbidden_strings = [
        "LSP Loop Exception",
        "write to closed file",
    ]

    for forbidden in forbidden_strings:
        assert forbidden not in combined_output, (
            f"Forbidden string '{forbidden}' found in test output. "
            f"This indicates LSP client lifecycle issues during shutdown."
        )
