#!/usr/bin/env python3
"""
DEPRECATED: Use scripts/install_FP.py instead.

This script is kept for backward compatibility only.
The new install_FP.py uses Clean Architecture patterns and
validators from src/infrastructure/validators.py.

Trifecta Multi-Repo Installer (Hub-Agnostic)

Arguments:
  --cli-root <path> : Path to trifecta_dope project (for running commands)
  --segment <path>  : Target segment path (repeatable)

Behavior:
  For each segment:
    1. Validates existence of skill/prime/agent/session
    2. Runs `trifecta ctx sync` (build + validate)
    3. Fails if segment is invalid

Migration: python scripts/install_FP.py --help
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


DEPRECATION_MESSAGE = (
    "DEPRECATED: scripts/install_trifecta_context.py is no longer supported. "
    "Use `uv run python scripts/install_FP.py --segment <path>` instead."
)


def run_command(cli_root: Path, cmd_args: List[str]) -> None:
    """Run uv command inside cli_root."""
    cmd = ["uv", "run", "trifecta"] + cmd_args
    print(f"🔄 Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cli_root, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Command failed:\n{result.stderr}")
        sys.exit(1)

    print(result.stdout)


def validate_segment(segment_path: Path) -> bool:
    """Check required files exist."""
    if not segment_path.exists():
        print(f"❌ Segment not found: {segment_path}")
        return False

    # Check strict ones
    if not (segment_path / "skill.md").exists():
        print(f"❌ Missing skill.md in {segment_path}")
        return False

    if not (segment_path / "_ctx" / "agent.md").exists():
        print(f"❌ Missing _ctx/agent.md in {segment_path}")
        return False

    return True


def main() -> None:
    print(DEPRECATION_MESSAGE)
    sys.exit(1)

    parser = argparse.ArgumentParser(description="Trifecta Context Installer")
    parser.add_argument("--cli-root", type=str, default=".", help="Path to trifecta_dope repo")
    parser.add_argument(
        "--segment", type=str, action="append", required=True, help="Target segment path"
    )

    args = parser.parse_args()

    cli_root = Path(args.cli_root).resolve()
    if not (cli_root / "pyproject.toml").exists():
        print(f"❌ Invalid CLI root (no pyproject.toml): {cli_root}")
        sys.exit(1)

    print(f"🔧 CLI Root: {cli_root}")

    for seg_str in args.segment:
        seg_path = Path(seg_str).resolve()
        print(f"\n📦 Processing Segment: {seg_path}")

        if not validate_segment(seg_path):
            sys.exit(1)

        print("   Running sync...")
        # Now using the strictly enforced --segment flag
        run_command(cli_root, ["ctx", "sync", "--segment", str(seg_path)])

    print("\n✅ All segments installed successfully.")


if __name__ == "__main__":
    main()
