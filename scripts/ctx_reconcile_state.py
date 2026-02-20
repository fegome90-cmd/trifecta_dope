#!/usr/bin/env python3
import argparse
import importlib
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys
from typing import Any, cast

CANONICAL_STATES = ["pending", "running", "done", "failed"]

# Import metadata inference module
from scripts.metadata_inference import infer_metadata_from_system

# NOTE:
# This script currently performs its own simple rollback via .bak restore.
# We intentionally avoid pretending we have transactional semantics unless
# we actually wire a real Transaction + rollback execution path.


def _ensure_deps():
    for module in ("yaml", "jsonschema"):
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            if os.environ.get("CTX_PY_REEXEC") == "1":
                raise
            repo_root = Path(__file__).resolve().parent.parent
            venv_python = repo_root / ".venv" / "bin" / "python"
            if venv_python.exists():
                env = os.environ.copy()
                env["CTX_PY_REEXEC"] = "1"
                os.execve(
                    str(venv_python),
                    [str(venv_python), __file__, *sys.argv[1:]],
                    env,
                )
            raise


_ensure_deps()
yaml = importlib.import_module("yaml")
validate = importlib.import_module("jsonschema").validate


@dataclass
class Issue:
    code: str
    severity: str
    wo_id: str | None
    paths: list[str]
    inferred: dict[str, Any] | None = None
    next_steps: list[str] | None = None


def load_yaml(path: Path) -> dict[str, Any] | None:
    data = yaml.safe_load(path.read_text())
    if data is None:
        return None
    return cast(dict[str, Any], data)


def load_schema(repo_root: Path, name: str) -> dict[str, Any]:
    schema_path = repo_root / "docs" / "backlog" / "schema" / name
    return cast(dict[str, Any], json.loads(schema_path.read_text()))


def iter_wo_files(repo_root: Path):
    for state in CANONICAL_STATES:
        wo_dir = repo_root / "_ctx" / "jobs" / state
        if not wo_dir.exists():
            continue
        for path in sorted(wo_dir.glob("*.yaml")):
            if "legacy" in path.parts:
                continue
            yield state, path


def read_worktrees(repo_root: Path, fixtures_root: Path | None) -> str:
    if fixtures_root is not None:
        wt_file = fixtures_root / "git_worktree_list.txt"
        if wt_file.exists():
            return wt_file.read_text()
        return ""
    result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_worktrees(text: str) -> set[str]:
    paths = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 1:
            paths.add(parts[0])
    return paths


def add_issue(
    issues: list[Issue], code: str, severity: str, wo_id: str | None, paths: list[str]
) -> None:
    issues.append(Issue(code=code, severity=severity, wo_id=wo_id, paths=paths))


def load_wo_index(repo_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for _, path in iter_wo_files(repo_root):
        try:
            wo = load_yaml(path)
        except Exception:
            continue
        if wo is None:
            continue
        wo_id = cast(str | None, wo.get("id"))
        if not wo_id:
            continue
        index[wo_id] = wo
    return index


def write_reconcile_log(repo_root: Path, issues: list[Issue], applied: bool) -> None:
    log_dir = repo_root / "_ctx" / "logs" / "reconcile"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [f"timestamp: {timestamp}", f"applied: {applied}", "issues:"]
    for issue in issues:
        lines.append(f"- {issue.code} {issue.wo_id} {issue.paths}")
    (log_dir / "reconcile.log").write_text("\n".join(lines) + "\n")


def check_running_metadata(
    wo: dict[str, Any],
    wo_path: Path,
    worktrees: set[str],
    repo_root: Path,
) -> Issue | None:
    """
    Check if WO in running/ has complete metadata.

    Args:
        wo: WO data dictionary
        wo_path: Path to WO YAML file
        worktrees: Set of worktree paths
        repo_root: Repository root

    Returns:
        Issue if metadata incomplete, None otherwise
    """
    required = {"status", "owner", "branch", "worktree", "started_at"}
    missing = [field for field in required if not wo.get(field)]

    if not missing:
        return None

    # Try to infer missing metadata
    wo_id = wo.get("id", wo_path.stem)
    result = infer_metadata_from_system(cast(str, wo_id), repo_root, set(missing))

    if result.success:
        # Return issue with inferred data for repair
        return Issue(
            code="RUNNING_WITHOUT_METADATA",
            severity="P1",
            wo_id=wo_id,
            paths=[str(wo_path)],
            inferred=result.inferred,
            next_steps=[],
        )
    else:
        # Cannot infer - return with errors
        return Issue(
            code="CANNOT_INFER_METADATA",
            severity="P1",  # P1 because we can't auto-repair but WO is still functional
            wo_id=wo_id,
            paths=[str(wo_path)],
            inferred=None,
            next_steps=result.errors,
        )


def repair_wo_metadata(wo_path: Path, inferred: dict[str, Any], root: Path) -> tuple[bool, str]:
    """
    Repair WO metadata with simple backup/restore rollback.

    Args:
        wo_path: Path to WO YAML file
        inferred: Dictionary of inferred metadata
        root: Repository root

    Returns:
        Tuple of (success, error_message)
    """
    backup_path = wo_path.with_suffix(".yaml.bak")

    try:
        # Create backup
        shutil.copy(wo_path, backup_path)

        # Load and update YAML
        wo = cast(dict[str, Any], yaml.safe_load(wo_path.read_text()))
        wo.update(inferred)

        # Validate against schema BEFORE writing
        schema = load_schema(root, "work_order.schema.json")
        try:
            validate(instance=wo, schema=schema)
        except Exception as e:
            raise ValueError(f"Repaired YAML fails schema validation: {str(e)}")

        # Atomic write: write to temp file then rename
        temp_path = wo_path.with_suffix(".yaml.tmp")
        temp_path.write_text(yaml.safe_dump(wo, sort_keys=False))
        temp_path.replace(wo_path)  # Atomic on POSIX

        # Verify backup is still there in case rollback needed
        if not backup_path.exists():
            # This shouldn't happen, but if it does, we can't rollback
            return False, "WARNING: Backup lost during repair (cannot rollback)"

        # Clean up backup on success
        backup_path.unlink()

        return True, ""

    except Exception as e:
        # Rollback
        try:
            if backup_path.exists():
                shutil.copy(backup_path, wo_path)
                backup_path.unlink()
        except Exception as rollback_error:
            return (
                False,
                f"Repair failed and rollback failed: {str(e)} | Rollback error: {str(rollback_error)}",
            )

        return False, str(e)


def maybe_record_patch(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        log_dir = repo_root / "_ctx" / "logs" / "reconcile"
        log_dir.mkdir(parents=True, exist_ok=True)
        patch_path = log_dir / "reconcile.patch"
        diff = subprocess.check_output(["git", "-C", str(repo_root), "diff"], text=True)
        patch_path.write_text(diff)
        return False
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-am", "chore: reconcile state"],
        check=False,
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Reconcile WO state vs locks and worktrees")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument(
        "--fixtures", default=None, help="Fixture name under tests/fixtures/reconcile"
    )
    parser.add_argument("--apply", action="store_true", help="Apply safe fixes")
    parser.add_argument("--force", action="store_true", help="Allow unsafe fixes")
    parser.add_argument("--json", dest="json_path", default=None, help="Write JSON report")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    fixtures_root: Path | None = None
    if args.fixtures:
        fixtures_root = repo_root / "tests" / "fixtures" / "reconcile" / args.fixtures
        repo_root = fixtures_root.resolve()

    worktree_text = read_worktrees(repo_root, fixtures_root)
    worktrees = parse_worktrees(worktree_text)

    schema = load_schema(repo_root, "work_order.schema.json")
    issues: list[Issue] = []
    wo_by_id: dict[str | None, list[Path]] = {}

    for state, path in iter_wo_files(repo_root):
        try:
            wo = load_yaml(path)
            if wo is None:
                raise ValueError("empty yaml")
            validate(instance=wo, schema=schema)
        except Exception:
            add_issue(issues, "WO_INVALID_SCHEMA", "P0", None, [str(path)])
            continue
        wo_id = cast(str | None, wo.get("id"))
        wo_by_id.setdefault(wo_id, []).append(path)

        if state == "running":
            lock_path = path.parent / f"{wo_id}.lock"
            if not lock_path.exists():
                add_issue(issues, "RUNNING_WITHOUT_LOCK", "P1", wo_id, [str(path)])
            worktree = wo.get("worktree")
            if worktree:
                worktree_path = str((repo_root / cast(str, worktree)).resolve())
                if worktree_path not in worktrees:
                    add_issue(issues, "RUNNING_WO_WITHOUT_WORKTREE", "P1", wo_id, [str(path)])

            # Check for incomplete metadata
            metadata_issue = check_running_metadata(wo, path, worktrees, repo_root)
            if metadata_issue:
                issues.append(metadata_issue)

    running_dir = repo_root / "_ctx" / "jobs" / "running"
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

    wo_index = load_wo_index(repo_root)
    for worktree in worktrees:
        wo_id = None
        for candidate_id, wo in wo_index.items():
            wt = wo.get("worktree")
            if wt and str((repo_root / cast(str, wt)).resolve()) == worktree:
                wo_id = candidate_id
                break
        if wo_id is None:
            add_issue(issues, "WORKTREE_WITHOUT_RUNNING_WO", "P1", None, [worktree])
        else:
            wo_path = repo_root / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
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
            elif issue.code == "RUNNING_WITHOUT_METADATA" and issue.inferred:
                wo_path = Path(issue.paths[0])
                success, error = repair_wo_metadata(wo_path, issue.inferred, repo_root)
                if not success:
                    print(f"Failed to repair {issue.wo_id}: {error}")
                    return 1
                print(f"Repaired metadata for {issue.wo_id}")
        write_reconcile_log(repo_root, issues, applied=True)
        maybe_record_patch(repo_root)
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
                "inferred": i.inferred,
                "next_steps": i.next_steps,
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
