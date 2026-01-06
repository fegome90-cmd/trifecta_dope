#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import yaml


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def load_dod_catalog(root: Path):
    dod_dir = root / "_ctx" / "dod"
    catalog = {}
    for path in sorted(dod_dir.glob("*.yaml")):
        dod_data = load_yaml(path)
        for entry in dod_data.get("dod", []):
            catalog[entry.get("id")] = entry
    return catalog


def main():
    parser = argparse.ArgumentParser(description="Finish a work order")
    parser.add_argument("wo_id", nargs="?", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--result", choices=["done", "failed"], default=None)
    args = parser.parse_args()

    if not args.wo_id:
        parser.print_help()
        return 0

    root = Path(args.root).resolve()
    running_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"
    if not running_path.exists():
        print(f"ERROR: missing WO {running_path}")
        return 1

    wo = load_yaml(running_path)
    dod_catalog = load_dod_catalog(root)
    dod = dod_catalog.get(wo.get("dod_id"))
    if not dod:
        print(f"ERROR: unknown dod_id {wo.get('dod_id')}")
        return 1

    required = dod.get("required_artifacts", [])
    handoff_dir = root / "_ctx" / "handoff" / args.wo_id
    missing = [name for name in required if not (handoff_dir / name).exists()]
    if missing:
        print("ERROR: missing artifacts:")
        for name in missing:
            print(name)
        return 1

    wo["result"] = args.result or "done"
    wo["finished_at"] = datetime.now(timezone.utc).isoformat()
    wo["commit_sha"] = subprocess.check_output([
        "git",
        "-C",
        str(root),
        "rev-parse",
        "HEAD",
    ], text=True).strip()

    dest_dir = root / "_ctx" / "jobs" / wo["result"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{args.wo_id}.yaml"
    write_yaml(dest_path, wo)
    running_path.unlink()

    lock_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.lock"
    if lock_path.exists():
        lock_path.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
