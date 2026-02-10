#!/usr/bin/env python3
"""
Trifecta Telemetry Rotation Script

Rotates _ctx/telemetry/events.jsonl when it exceeds thresholds.
Usage:
    python scripts/telemetry_rotate.py
    TRIFECTA_TELEMETRY_DIR=/custom/path python scripts/telemetry_rotate.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path


# Configuration
MAX_EVENTS = 1000  # Rotate after this many events
MAX_SIZE_MB = 10   # Rotate after this many MB


def get_telemetry_dir() -> Path:
    """Resolve telemetry directory from env or default."""
    if env_dir := os.environ.get("TRIFECTA_TELEMETRY_DIR"):
        return Path(env_dir)
    # Default: _ctx/telemetry from repo root
    repo_root = Path(__file__).parent.parent
    return repo_root / "_ctx" / "telemetry"


def count_events(events_file: Path) -> int:
    """Count number of newline-delimited JSON events."""
    if not events_file.exists():
        return 0
    count = 0
    with open(events_file, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


def get_size_mb(events_file: Path) -> float:
    """Get file size in MB."""
    if not events_file.exists():
        return 0.0
    return events_file.stat().st_size / (1024 * 1024)


def rotate_events(events_file: Path) -> None:
    """
    Rotate events.jsonl with timestamp suffix.

    New format: events.YYYYMMDD_HHMMSS.size.jsonl.rotated
    Example: events.20260210_143022.12.5.jsonl.rotated
    """
    if not events_file.exists():
        print(f"No events file found at {events_file}")
        return

    # Gather metrics for filename
    size_mb = get_size_mb(events_file)
    event_count = count_events(events_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build new filename
    base_name = events_file.stem  # "events" without .jsonl
    rotated_name = f"{base_name}.{timestamp}.{size_mb:.1f}.jsonl.rotated"
    rotated_path = events_file.parent / rotated_name

    # Rename
    events_file.rename(rotated_path)

    print(f"Rotated telemetry file:")
    print(f"  From: {events_file}")
    print(f"  To:   {rotated_path}")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Events: {event_count}")


def main() -> int:
    telemetry_dir = get_telemetry_dir()
    events_file = telemetry_dir / "events.jsonl"

    if not events_file.exists():
        print(f"No events file at {events_file} - nothing to rotate")
        return 0

    # Check thresholds
    event_count = count_events(events_file)
    size_mb = get_size_mb(events_file)

    should_rotate = event_count >= MAX_EVENTS or size_mb >= MAX_SIZE_MB

    if not should_rotate:
        print(f"Telemetry file within thresholds:")
        print(f"  Events: {event_count}/{MAX_EVENTS}")
        print(f"  Size: {size_mb:.2f} MB/{MAX_SIZE_MB} MB")
        print(f"No rotation needed.")
        return 0

    # Rotation needed
    print(f"Telemetry file exceeds thresholds:")
    print(f"  Events: {event_count}/{MAX_EVENTS}")
    print(f"  Size: {size_mb:.2f} MB/{MAX_SIZE_MB} MB")
    print()

    # Confirm unless --force flag
    if "--force" not in sys.argv:
        response = input("Rotate now? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("Aborted.")
            return 1

    rotate_events(events_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
