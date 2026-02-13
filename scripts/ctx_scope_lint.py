#!/usr/bin/env python3
import argparse
from pathlib import Path
import fnmatch
import subprocess
import sys
import yaml


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def list_changed_files(root: Path):
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:]
        if path:
            changed.append(path)
    return changed


def is_allowed(path: str, allow, deny):
    for pattern in deny:
        if fnmatch.fnmatch(path, pattern):
            return False
    if not allow:
        return False
    for pattern in allow:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Scope linter for WO changes")
    parser.add_argument("wo_id", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    wo_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        wo_path = root / "_ctx" / "jobs" / "pending" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        print(f"ERROR: missing WO {wo_path}")
        return 1

    wo = load_yaml(wo_path)
    scope = wo.get("scope", {})
    allow = scope.get("allow", [])
    deny = scope.get("deny", [])

    violations = []
    for path in list_changed_files(root):
        if not is_allowed(path, allow, deny):
            violations.append(path)

    if violations:
        print("SCOPE_VIOLATIONS:")
        for path in violations:
            print(path)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
