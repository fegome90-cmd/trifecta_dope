#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys
import yaml
from jsonschema import validate

CANONICAL_STATES = ["pending", "running", "done", "failed"]


@dataclass
class Issue:
    code: str
    severity: str
    wo_id: str | None
    paths: list[str]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def load_schema(root: Path, name: str):
    return json.loads((root / "docs" / "backlog" / "schema" / name).read_text())


def iter_wo_files(root: Path):
    for state in CANONICAL_STATES:
        wo_dir = root / "_ctx" / "jobs" / state
        if not wo_dir.exists():
            continue
        for path in sorted(wo_dir.glob("*.yaml")):
            if "legacy" in path.parts:
                continue
            yield state, path


def read_worktrees(root: Path, fixtures: Path | None):
    if fixtures is not None:
        wt_file = fixtures / "git_worktree_list.txt"
        if wt_file.exists():
            return wt_file.read_text()
        return ""
    result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_worktrees(text: str):
    paths = set()
    for line in text.splitlines():
        if line.startswith("worktree "):
            parts = line.split()
            if len(parts) >= 2:
                paths.add(parts[1])
    return paths


def add_issue(issues, code, severity, wo_id, paths):
    issues.append(Issue(code=code, severity=severity, wo_id=wo_id, paths=paths))


def load_wo_index(root: Path):
    index = {}
    for _, path in iter_wo_files(root):
        try:
            wo = load_yaml(path)
        except Exception:
            continue
        wo_id = wo.get("id")
        if not wo_id:
            continue
        index[wo_id] = wo
    return index


def write_reconcile_log(root: Path, issues, applied):
    log_dir = root / "_ctx" / "logs" / "reconcile"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [f"timestamp: {timestamp}", f"applied: {applied}", "issues:"]
    for issue in issues:
        lines.append(f"- {issue.code} {issue.wo_id} {issue.paths}")
    (log_dir / "reconcile.log").write_text("\n".join(lines) + "\n")


def maybe_record_patch(root: Path):
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        patch_path = root / "_ctx" / "logs" / "reconcile" / "reconcile.patch"
        diff = subprocess.check_output(
            ["git", "-C", str(root), "diff"], text=True
        )
        patch_path.write_text(diff)
        return False
    subprocess.run(
        ["git", "-C", str(root), "commit", "-am", "chore: reconcile state"],
        check=False,
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Reconcile WO state vs locks and worktrees")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--fixtures", default=None, help="Fixture name under tests/fixtures/reconcile")
    parser.add_argument("--apply", action="store_true", help="Apply safe fixes")
    parser.add_argument("--force", action="store_true", help="Allow unsafe fixes")
    parser.add_argument("--json", dest="json_path", default=None, help="Write JSON report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    fixtures_root = None
    if args.fixtures:
        fixtures_root = root / "tests" / "fixtures" / "reconcile" / args.fixtures
        root = fixtures_root

    worktree_text = read_worktrees(root, fixtures_root)
    worktrees = parse_worktrees(worktree_text)

    schema = load_schema(root, "work_order.schema.json")
    issues = []
    wo_by_id = {}

    for state, path in iter_wo_files(root):
        try:
            wo = load_yaml(path)
            validate(instance=wo, schema=schema)
        except Exception:
            add_issue(issues, "WO_INVALID_SCHEMA", "P0", None, [str(path)])
            continue
        wo_id = wo.get("id")
        wo_by_id.setdefault(wo_id, []).append(path)

        if state == "running":
            lock_path = path.parent / f"{wo_id}.lock"
            if not lock_path.exists():
                add_issue(issues, "RUNNING_WITHOUT_LOCK", "P1", wo_id, [str(path)])
            worktree = wo.get("worktree")
            if worktree:
                worktree_path = str((root / worktree).resolve())
                if worktree_path not in worktrees:
                    add_issue(issues, "RUNNING_WO_WITHOUT_WORKTREE", "P1", wo_id, [str(path)])

    running_dir = root / "_ctx" / "jobs" / "running"
    if running_dir.exists():
        for lock_path in running_dir.glob("*.lock"):
            wo_id = lock_path.stem
            wo_path = running_dir / f"{wo_id}.yaml"
            if not wo_path.exists():
                add_issue(issues, "LOCK_WITHOUT_RUNNING_WO", "P1", wo_id, [str(lock_path)])

    for wo_id, paths in wo_by_id.items():
        if wo_id is None:
            continue
        if len(paths) > 1:
            add_issue(issues, "DUPLICATE_WO_ID", "P0", wo_id, [str(p) for p in paths])

    wo_index = load_wo_index(root)
    for worktree in worktrees:
        wo_id = None
        for candidate_id, wo in wo_index.items():
            wt = wo.get("worktree")
            if wt and str((root / wt).resolve()) == worktree:
                wo_id = candidate_id
                break
        if wo_id is None:
            add_issue(issues, "WORKTREE_WITHOUT_RUNNING_WO", "P1", None, [worktree])
        else:
            wo_path = root / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
            if not wo_path.exists():
                add_issue(issues, "WORKTREE_WITHOUT_RUNNING_WO", "P1", wo_id, [worktree])

    apply_refused = any(issue.code == "WO_INVALID_SCHEMA" for issue in issues)
    if args.apply and apply_refused:
        print("apply refused: WO_INVALID_SCHEMA")
        return 1

    if args.apply:
        for issue in issues:
            if issue.code == "RUNNING_WITHOUT_LOCK":
                lock_path = Path(issue.paths[0]).with_suffix(".lock")
                lock_path.write_text(f"{issue.wo_id}\n")
        write_reconcile_log(root, issues, applied=True)
        maybe_record_patch(root)
    else:
        if any(issue.code == "RUNNING_WITHOUT_LOCK" for issue in issues):
            print("would_create_lock")

    report = {
        "issues": [
            {
                "code": i.code,
                "severity": i.severity,
                "wo_id": i.wo_id,
                "paths": i.paths,
            }
            for i in issues
        ]
    }

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, indent=2))

    if issues:
        for issue in issues:
            print(issue.code)
        if any(issue.severity == "P0" for issue in issues):
            return 1

    if args.apply and any(issue.code == "RUNNING_WO_WITHOUT_WORKTREE" for issue in issues):
        if not args.force:
            print("requires --force")
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
