#!/usr/bin/env python3
"""Analyze AST cache adoption metrics from telemetry events.

Usage:
    python eval/scripts/analyze_adoption_telemetry.py --segment . --days 7 --out _ctx/metrics/wo0013_adoption.json
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def load_telemetry_events(events_path: Path) -> list[dict[str, Any]]:
    """Load all events from events.jsonl, skipping malformed lines."""
    events = []
    with open(events_path) as f:
        for line in f:
            line = line.strip()
            if not line or line == "[]":
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    return events


def filter_events_by_days(events: list[dict], days: int) -> list[dict]:
    """Filter events to last N days based on timestamp."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [e for e in events if e.get("ts", "") >= cutoff]


def main():
    parser = argparse.ArgumentParser(description="Analyze AST cache adoption from telemetry")
    parser.add_argument("--segment", default=".", help="Segment path (default: .)")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze (default: 7)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--telemetry-file",
        default="_ctx/telemetry/events.jsonl",
        help="Path to events.jsonl"
    )
    args = parser.parse_args()

    segment_path = Path(args.segment).resolve()
    telemetry_path = segment_path / args.telemetry_file

    if not telemetry_path.exists():
        logging.error(f"Telemetry file not found: {telemetry_path}")
        sys.exit(1)

    logging.info(f"Loading telemetry from {telemetry_path}...")
    all_events = load_telemetry_events(telemetry_path)

    logging.info(f"Filtering events from last {args.days} days...")
    events = filter_events_by_days(all_events, args.days)

    logging.info(f"Analyzing {len(events)} events...")
    metrics = analyze_adoption_metrics(events, segment_path)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logging.info(f"Metrics written to {out_path}")
    print(json.dumps(metrics, indent=2))


def analyze_adoption_metrics(events: list[dict], segment_path: Path) -> dict[str, Any]:
    """Analyze adoption metrics from filtered events."""
    # Placeholder - implement in next task
    return {"placeholder": True}


if __name__ == "__main__":
    setup_logging()
    main()
