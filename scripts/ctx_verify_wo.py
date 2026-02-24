#!/usr/bin/env python3
"""
Scoped WO Verification - Execute WO-specific verify.commands only.

HARD RULES:
- Search WO in (running, pending, failed, done) - all 4 states
- FAIL (exit 2) if WO appears in >1 state (split-brain)
- FAIL (exit 2) if WO has no verify.commands defined (NO fallback PASS)
- Return exit 0 only if ALL commands pass
- Return exit 1 if any command fails

This script does NOT run the global test suite (unit/integration/acceptance).
Those gates belong in CI (make gate-all) or scripts/verify.sh.

Usage:
    uv run python scripts/ctx_verify_wo.py WO-XXXX [--root PATH] [--json PATH]

Exit codes:
    0: All WO verify.commands passed
    1: One or more commands failed
    2: Usage error (missing WO, split-brain, no commands)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# All states where WO YAML can exist
WO_STATES = ("running", "pending", "done", "failed")


def load_wo_yaml(root: Path, wo_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Load WO YAML from any state directory.

    Returns:
        (wo_data, found_states) - wo_data is None if not found,
        found_states lists all states where WO was found.
    """
    found_states: list[str] = []
    wo_data: dict[str, Any] | None = None

    for state in WO_STATES:
        path = root / "_ctx" / "jobs" / state / f"{wo_id}.yaml"
        if path.exists():
            found_states.append(state)
            if wo_data is None:
                try:
                    wo_data = yaml.safe_load(path.read_text())
                except yaml.YAMLError as e:
                    print(f"ERROR: Failed to parse {path}: {e}", file=sys.stderr)
                    return None, found_states
                except OSError as e:
                    print(f"ERROR: Failed to read {path}: {e}", file=sys.stderr)
                    return None, found_states

    return wo_data, found_states


def get_verify_commands(wo: dict[str, Any]) -> list[str]:
    """
    Extract verify.commands from WO YAML.

    HARD RULE: If no commands defined, return empty list (caller must FAIL).
    NO fallback PASS allowed.
    """
    verify = wo.get("verify", {})
    commands = verify.get("commands", [])
    return commands if commands else []


def run_command(cmd: str, log_dir: Path, index: int, timeout: int = 300) -> tuple[bool, str, float]:
    """
    Run a single verify command.

    Returns:
        (passed, output, duration_seconds)
    """
    log_file = log_dir / f"command_{index:02d}.log"

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.monotonic() - start

        output = f"COMMAND: {cmd}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nEXIT CODE: {result.returncode}"
        log_file.write_text(output)

        passed = result.returncode == 0
        return passed, output, duration

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        output = f"COMMAND: {cmd}\n\nTIMEOUT after {timeout}s"
        log_file.write_text(output)
        return False, output, duration
    except Exception as e:
        duration = time.monotonic() - start
        output = f"COMMAND: {cmd}\n\nERROR: {e}"
        log_file.write_text(output)
        return False, output, duration


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scoped WO Verification - Execute WO-specific verify.commands only"
    )
    parser.add_argument("wo_id", help="Work Order ID (WO-XXXX)")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", help="Output JSON report to file")
    parser.add_argument("--timeout", type=int, default=300, help="Per-command timeout (seconds)")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    # Load WO from all states
    wo, found_states = load_wo_yaml(root, args.wo_id)

    # CASE 1: WO not found
    if wo is None:
        print(f"ERROR: WO {args.wo_id} not found in any state", file=sys.stderr)
        return 2

    # CASE 2: Split-brain detected
    if len(found_states) > 1:
        print(f"ERROR: SPLIT-BRAIN detected for {args.wo_id}", file=sys.stderr)
        print(f"  Found in states: {found_states}", file=sys.stderr)
        print(f"  ACTION: Run /wo-repair to reconcile state", file=sys.stderr)
        return 2

    # CASE 3: No verify.commands defined (HARD RULE: NO fallback PASS)
    commands = get_verify_commands(wo)
    if not commands:
        print(f"ERROR: No verify.commands defined for {args.wo_id}", file=sys.stderr)
        print(f"  HARD RULE: Missing verify.commands -> FAIL (no fallback PASS)", file=sys.stderr)
        print(f"  ACTION: Add verify.commands to WO YAML", file=sys.stderr)
        return 2

    # Setup log directory
    log_dir = root / "_ctx" / "logs" / args.wo_id
    log_dir.mkdir(parents=True, exist_ok=True)

    # Run commands
    results: list[dict[str, Any]] = []
    all_passed = True

    print(f"=== Scoped WO Verification: {args.wo_id} ===")
    print(f"State: {found_states[0]}")
    print(f"Commands: {len(commands)}")
    print()

    for i, cmd in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] {cmd[:70]}{'...' if len(cmd) > 70 else ''}")
        passed, output, duration = run_command(cmd, log_dir, i, args.timeout)
        results.append({
            "command": cmd,
            "passed": passed,
            "output": output[:500] if len(output) > 500 else output,
            "duration_seconds": round(duration, 2),
        })

        if passed:
            print(f"  PASS ({duration:.1f}s)")
        else:
            print(f"  FAIL ({duration:.1f}s)")
            all_passed = False

    # Build verdict
    verdict = {
        "wo_id": args.wo_id,
        "status": "PASS" if all_passed else "FAIL",
        "state": found_states[0],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commands_run": len(commands),
        "commands_passed": sum(1 for r in results if r["passed"]),
        "commands_failed": sum(1 for r in results if not r["passed"]),
        "total_duration_seconds": round(sum(r["duration_seconds"] for r in results), 2),
        "results": results,
    }

    # Write verdict
    verdict_file = log_dir / "scoped_verdict.json"
    verdict_file.write_text(json.dumps(verdict, indent=2))

    print()
    print(f"Verdict: {verdict['status']}")
    print(f"Report: {verdict_file}")

    if args.json:
        Path(args.json).write_text(json.dumps(verdict, indent=2))
        print(f"JSON: {args.json}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
