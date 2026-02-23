#!/usr/bin/env python3
"""WO-scoped verify - runs only WO-related tests from verify.commands."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def get_wo_verify_commands(wo_yaml: Path) -> list[str]:
    """Extract verify commands from WO YAML."""
    data = yaml.safe_load(wo_yaml.read_text())
    return data.get("verify", {}).get("commands", [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run WO-scoped verify commands from WO YAML"
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
        print("No verify.commands found in WO YAML")
        return 0

    print(f"=== WO-Scoped Verify: {args.wo_id} ===")
    print(f"Commands: {len(commands)}")
    print()

    for i, cmd in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=root)
        if result.returncode != 0:
            print(f"FAILED: {cmd}")
            return 1

    print()
    print("=== ALL VERIFIED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
