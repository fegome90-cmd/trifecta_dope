#!/usr/bin/env python3
"""
Trifecta Telemetry Rotation Script

Rotates _ctx/telemetry/events.jsonl when it exceeds thresholds.
Usage:
    python scripts/telemetry_rotate.py
    TRIFECTA_TELEMETRY_DIR=/custom/path python scripts/telemetry_rotate.py
    python scripts/telemetry_rotate.py --force
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

# Import Result type for functional error handling
if TYPE_CHECKING:
    from src.domain.result import Result
else:
    # Runtime import to avoid circular dependency in tests
    from src.domain.result import Ok, Err, Result


# Configuration
MAX_EVENTS: int = 1000  # Rotate after this many events
MAX_SIZE_MB: int = 10  # Rotate after this many MB


@dataclass(frozen=True)
class RotationResult:
    """Result of a successful rotation operation."""

    from_path: Path
    to_path: Path
    size_mb: float
    event_count: int


def get_telemetry_dir() -> Path:
    """Resolve telemetry directory from env or default."""
    if env_dir := os.environ.get("TRIFECTA_TELEMETRY_DIR"):
        return Path(env_dir).resolve()
    # Use shared repo_root() from scripts.paths
    from scripts.paths import repo_root

    return repo_root() / "_ctx" / "telemetry"


def count_events(events_file: Path) -> Result[int, str]:
    """Count number of newline-delimited JSON events.

    Returns:
        Ok[count] on success, Err[error_message] on failure.
    """
    if not events_file.exists():
        return Ok(0)

    try:
        count = 0
        with open(events_file, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return Ok(count)
    except PermissionError:
        return Err(f"Permission denied reading {events_file}")
    except UnicodeDecodeError:
        return Err(f"File encoding error in {events_file} (expected UTF-8)")
    except OSError as e:
        return Err(f"OS error reading {events_file}: {e}")


def get_size_mb(events_file: Path) -> Result[float, str]:
    """Get file size in MB.

    Returns:
        Ok[size_mb] on success, Err[error_message] on failure.
    """
    if not events_file.exists():
        return Ok(0.0)

    try:
        size = events_file.stat().st_size
        return Ok(size / (1024 * 1024))
    except PermissionError:
        return Err(f"Permission denied accessing {events_file}")
    except OSError as e:
        return Err(f"OS error getting size of {events_file}: {e}")


def rotate_events(events_file: Path) -> Result[RotationResult, str]:
    """
    Rotate events.jsonl with timestamp suffix.

    New format: events.YYYYMMDD_HHMMSS.size.jsonl.rotated
    Example: events.20260210_143022.12.5.jsonl.rotated

    Returns:
        Ok[RotationResult] on success, Err[error_message] on failure.
    """
    if not events_file.exists():
        return Err(f"No events file found at {events_file}")

    try:
        # Gather metrics for filename
        size_result = get_size_mb(events_file)
        if isinstance(size_result, Err):
            return size_result
        size_mb = size_result.unwrap()

        count_result = count_events(events_file)
        if isinstance(count_result, Err):
            return count_result
        event_count = count_result.unwrap()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build new filename
        base_name = events_file.stem  # "events" without .jsonl
        rotated_name = f"{base_name}.{timestamp}.{size_mb:.1f}.jsonl.rotated"
        rotated_path = events_file.parent / rotated_name

        # Rename
        events_file.rename(rotated_path)

        return Ok(
            RotationResult(
                from_path=events_file,
                to_path=rotated_path,
                size_mb=size_mb,
                event_count=event_count,
            )
        )
    except PermissionError:
        return Err(f"Permission denied: Cannot write to {events_file.parent}")
    except FileExistsError:
        return Err(f"Target file already exists: {rotated_path}")
    except OSError as e:
        return Err(f"Filesystem error rotating telemetry: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Rotate Trifecta telemetry files")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    telemetry_dir = get_telemetry_dir()
    events_file = telemetry_dir / "events.jsonl"

    if not events_file.exists():
        print(f"No events file at {events_file} - nothing to rotate")
        return 0

    # Check thresholds
    count_result = count_events(events_file)
    size_result = get_size_mb(events_file)

    # Handle errors from threshold checking
    if isinstance(count_result, Err):
        print(f"Error: {count_result.unwrap_err()}", file=sys.stderr)
        return 1
    if isinstance(size_result, Err):
        print(f"Error: {size_result.unwrap_err()}", file=sys.stderr)
        return 1

    event_count = count_result.unwrap()
    size_mb = size_result.unwrap()

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
    if not args.force:
        try:
            response = input("Rotate now? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                print("Aborted.")
                return 1
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1

    result = rotate_events(events_file)
    if isinstance(result, Err):
        print(f"Error: {result.unwrap_err()}", file=sys.stderr)
        return 1

    rotated = result.unwrap()
    print(f"Rotated telemetry file:")
    print(f"  From: {rotated.from_path}")
    print(f"  To:   {rotated.to_path}")
    print(f"  Size: {rotated.size_mb:.2f} MB")
    print(f"  Events: {rotated.event_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
