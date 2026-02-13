#!/usr/bin/env python3
import argparse
import fnmatch
from pathlib import Path
import subprocess
import sys
import yaml


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text())
    except (yaml.YAMLError, OSError) as exc:
        raise SystemExit(f"ERROR: failed to load WO YAML: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("ERROR: WO YAML must be a mapping")
    return data


def git_paths(root: Path) -> list[str]:
    # Enforce what matters: staged + unstaged diffs (not porcelain parsing)
    paths: set[str] = set()

    for args in (["git", "diff", "--name-only", "--cached"], ["git", "diff", "--name-only"]):
        p = subprocess.run(args, cwd=root, capture_output=True, text=True)
        if p.returncode != 0:
            raise SystemExit(f"ERROR: git diff failed: {p.stderr.strip()}")
        for line in p.stdout.splitlines():
            line = line.strip()
            if line:
                paths.add(line)

    # Optionally include untracked files that might be added
    p = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, capture_output=True, text=True)
    if p.returncode == 0:
        for line in p.stdout.splitlines():
            line = line.strip()
            if line:
                paths.add(line)

    return sorted(paths)


def is_denied(path: str, deny: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in deny)


def is_allowed(path: str, allow: list[str], deny: list[str]) -> bool:
    # Deny always wins (fail-closed)
    if is_denied(path, deny):
        return False

    # No allow list => deny everything
    if not allow:
        return False

    # Fast-path: global allow patterns
    if any(pat in ("*", "**/*", "*/**") for pat in allow):
        return True

    # Normal match
    for pat in allow:
        if fnmatch.fnmatch(path, pat):
            return True
        # support prefix-ish patterns like "dir/**"
        if pat.endswith("/**") and path.startswith(pat[:-3]):
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Scope linter for WO changes")
    parser.add_argument("wo_id", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    wo_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        wo_path = root / "_ctx" / "jobs" / "pending" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        print(f"ERROR: missing WO {wo_path}", file=sys.stderr)
        return 1

    wo = load_yaml(wo_path)
    scope = wo.get("scope", {}) or {}
    allow = scope.get("allow", []) or []
    deny = scope.get("deny", []) or []

    violations: list[str] = []
    for path in git_paths(root):
        if not is_allowed(path, allow, deny):
            violations.append(path)

    if violations:
        print("SCOPE_VIOLATIONS:")
        for v in violations:
            print(v)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
