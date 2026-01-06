#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import yaml


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def parse_time(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def iter_wos(root: Path):
    states = ["pending", "running", "done", "failed"]
    for state in states:
        wo_dir = root / "_ctx" / "jobs" / state
        if not wo_dir.exists():
            continue
        for path in sorted(wo_dir.glob("*.yaml")):
            yield state, path


def main():
    parser = argparse.ArgumentParser(description="Show WO status summary")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--stale-days", type=int, default=7)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    stale = []
    now = datetime.now(timezone.utc)

    for state, path in iter_wos(root):
        counts[state] += 1
        if state == "running":
            wo = load_yaml(path)
            started = parse_time(wo.get("started_at"))
            if started and (now - started).days >= args.stale_days:
                stale.append(path.name)

    print("WO status summary")
    for key in ["pending", "running", "done", "failed"]:
        print(f"{key}: {counts[key]}")

    if stale:
        print("stale:")
        for wo in stale:
            print(f"- {wo}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
