#!/usr/bin/env python3
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path


def load_jsonl(path: Path):
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
    return entries


def main():
    parser = argparse.ArgumentParser(description="Report WO metrics")
    parser.add_argument("--root", default=".")
    parser.add_argument("--since", default=None, help="ISO date filter")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    metrics_path = root / "_ctx" / "metrics" / "wo_metrics.jsonl"
    entries = load_jsonl(metrics_path)

    if args.since:
        since = datetime.fromisoformat(args.since)
        filtered = []
        for entry in entries:
            ts = entry.get("timestamp")
            if ts and datetime.fromisoformat(ts) >= since:
                filtered.append(entry)
        entries = filtered

    counts = Counter(e.get("result") for e in entries if e.get("result"))
    total = sum(counts.values())

    print("WO metrics report")
    print(f"total: {total}")
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
