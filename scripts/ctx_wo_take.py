#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import getpass
import json
from pathlib import Path
import subprocess
import sys
import yaml
from jsonschema import validate


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def load_schema(root: Path, name: str):
    schema_path = root / "docs" / "backlog" / "schema" / name
    return json.loads(schema_path.read_text())


def ensure_worktree(root: Path, wo_id: str, branch: str, worktree: str):
    if not branch or not worktree:
        return
    worktree_path = (root / worktree).resolve()
    if worktree_path.exists():
        return
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree_path)],
        cwd=root,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Take a work order and move it to running")
    parser.add_argument("wo_id", nargs="?", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--owner", default=None, help="Owner name")
    args = parser.parse_args()

    if not args.wo_id:
        parser.print_help()
        return 0

    root = Path(args.root).resolve()
    job_path = root / "_ctx" / "jobs" / "pending" / f"{args.wo_id}.yaml"
    if not job_path.exists():
        print(f"ERROR: missing WO {job_path}")
        return 1

    wo = load_yaml(job_path)
    schema = load_schema(root, "work_order.schema.json")
    validate(instance=wo, schema=schema)

    backlog = load_yaml(root / "_ctx" / "backlog" / "backlog.yaml")
    epic_ids = {e.get("id") for e in backlog.get("epics", [])}
    if wo.get("epic_id") not in epic_ids:
        print(f"ERROR: unknown epic_id {wo.get('epic_id')}")
        return 1

    owner = args.owner or getpass.getuser()
    wo["owner"] = owner
    wo["status"] = "running"
    wo["started_at"] = datetime.now(timezone.utc).isoformat()

    ensure_worktree(root, args.wo_id, wo.get("branch"), wo.get("worktree"))

    running_dir = root / "_ctx" / "jobs" / "running"
    running_dir.mkdir(parents=True, exist_ok=True)
    running_path = running_dir / f"{args.wo_id}.yaml"
    write_yaml(running_path, wo)
    job_path.unlink()

    lock_path = running_dir / f"{args.wo_id}.lock"
    lock_path.write_text(f"{args.wo_id}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
