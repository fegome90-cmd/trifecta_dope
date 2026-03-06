#!/usr/bin/env python3
"""WO-scoped verify - runs only WO-related tests from verify.commands.

CONTRACT
========

What it runs:
--------------
- Commands from WO YAML: `verify.commands` list
- Typically: `uv run pytest -q tests/unit/test_xxx.py`
- Unit tests and linters SCOPED to the WO's scope

What it does NOT run:
--------------------
- Full test suite (all 1195+ tests)
- Integration tests unrelated to WO
- Tests for other subsystems
- Global invariant checks (use full verify.sh for that)

How scope is determined:
-----------------------
- By the WO YAML's `verify.commands` field
- If empty, returns success (nothing to verify)

Exit codes:
-----------
- 0: All verify commands passed (or no commands defined)
- 1: WO not found OR one or more commands failed

Usage:
------
    uv run python scripts/ctx_verify_wo.py WO-XXXX
    uv run python scripts/ctx_verify_wo.py WO-XXXX --root /path/to/repo

Integration with /wo-finish:
---------------------------
This script allows closing a WO without running the full suite.
The full suite is reserved for releases/merges, not WO closures.

Gate separation:
- Gate WO (local): this script → must pass for /wo-finish
- Gate Release (global): verify.sh → must pass for merge/release

Design rationale:
----------------
The 8 unrelated test failures that blocked WO-0015 closure demonstrated
that mixing "local quality" with "global debt" creates a throughput prison.
This script separates those concerns: WO closure only requires WO-scoped tests.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def get_wo_verify_commands(wo_yaml: Path) -> list[str]:
    """Extract verify commands from WO YAML.

    Handles multiple formats:
    - list of strings: ["cmd1", "cmd2"]
    - single string: "cmd1" (converted to list)
    - missing/invalid: [] (empty list)
    """
    data = yaml.safe_load(wo_yaml.read_text())
    if data is None:
        return []
    commands = data.get("verify", {}).get("commands", [])
    if isinstance(commands, str):
        return [commands]
    if not isinstance(commands, list):
        return []
    return [str(c) for c in commands if c is not None]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run WO-scoped verify commands from WO YAML",
        epilog="""
Examples:
  # Run verify for WO-0015
  uv run python scripts/ctx_verify_wo.py WO-0015

  # With explicit root
  uv run python scripts/ctx_verify_wo.py WO-0015 --root /path/to/repo

Note: This runs ONLY the commands in WO YAML verify.commands field.
It does NOT run the full test suite. Use for WO closure, not releases.

Gate separation:
  - Gate WO (local): this script
  - Gate Release (global): scripts/verify.sh
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("wo_id", help="WO-XXXX")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    wo_yaml = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"

    if not wo_yaml.exists():
        print(f"ERROR: {wo_yaml} not found")
        return 1

    commands = get_wo_verify_commands(wo_yaml)

    if not commands:
        # WARNING: Empty verify.commands bypasses WO closure gates.
        # ctx_wo_lint.py enforces non-empty verify.commands (WO009).
        # If you see this warning, the WO may not have been properly linted.
        print("⚠️  WARNING: No verify.commands found in WO YAML")
        print("   This bypasses verification gates. Ensure WO was linted with ctx_wo_lint.py")
        print("   Returning success for backward compatibility, but this may indicate a problem.")
        return 0

    print(f"=== WO-Scoped Verify: {args.wo_id} ===")
    print(f"Commands: {len(commands)}")
    print()

    for i, cmd in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] {cmd}")
        # NOTE: shell=True is used here because commands are developer-defined
        # in WO YAML files, not user input. The security risk is acceptable
        # because WO YAMLs are version-controlled and reviewed.
        result = subprocess.run(cmd, shell=True, cwd=root)
        if result.returncode != 0:
            print(f"FAILED: {cmd}")
            return 1

    print()
    print("=== ALL VERIFIED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
