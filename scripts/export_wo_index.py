#!/usr/bin/env python3
"""Export WO worktree index for Sidecar integration."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    return yaml.safe_load(path.read_text())


def get_repo_root() -> Path:
    """Get repository root path."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return Path(result.stdout.strip())


def get_git_head_sha(root: Path) -> str:
    """Get current git HEAD SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def get_worktrees_from_git(root: Path) -> dict:
    """Parse git worktree list output.

    Returns dict mapping branch name to worktree info.
    """
    worktrees = {}
    try:
        output = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"],
            cwd=root, text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return worktrees

    current = {}
    for line in output.splitlines():
        if not line:
            if current.get("worktree"):
                branch = current.get("branch", "")
                branch = branch.replace("refs/heads/", "")
                if branch:
                    wt_path = current["worktree"]
                    worktrees[branch] = {
                        "path": wt_path,
                        "HEAD": current.get("HEAD", ""),
                    }
            current = {}
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            current[parts[0]] = parts[1]
        else:
            current[parts[0]] = ""

    return worktrees


def build_wo_index(wo_file: Path, root: Path, worktrees: dict) -> dict:
    """Build WO entry for index."""
    wo = load_yaml(wo_file)
    wo_id = wo["id"]
    status = wo.get("status", "pending")

    # Get branch from YAML or infer from WO ID
    branch = wo.get("branch", f"feat/wo-{wo_id}")

    # Check if worktree exists in git
    worktree_exists = branch in worktrees
    worktree_head_sha = None
    worktree_path = None

    if worktree_exists:
        wt = worktrees[branch]
        # Git can return absolute OR relative paths
        wt_path = Path(wt["path"])
        wt_abs = wt_path if wt_path.is_absolute() else (root / wt_path).resolve()
        worktree_path = os.path.relpath(wt_abs, root)
        worktree_head_sha = wt.get("HEAD", "")
    else:
        # Infer path from WO ID using scripts.paths
        import sys
        sys.path.insert(0, str(root / "scripts"))
        from paths import get_worktree_path
        inferred_abs = get_worktree_path(root, wo_id)
        worktree_path = os.path.relpath(inferred_abs, root)

    # WO YAML path relative to repo_root
    wo_yaml_path = f"_ctx/jobs/{status}/{wo_id}.yaml"

    return {
        "id": wo_id,
        "title": wo.get("title", ""),
        "status": status,
        "priority": wo.get("priority", "medium"),
        "owner": wo.get("owner", ""),
        "epic_id": wo.get("epic_id", ""),
        "worktree_path": worktree_path,
        "worktree_exists": worktree_exists,
        "branch": branch,
        "worktree_head_sha": worktree_head_sha,
        "wo_yaml_path": wo_yaml_path,
        "created_at": wo.get("created_at", ""),
        "closed_at": wo.get("closed_at"),
        "last_error": None
    }


def main():
    root = get_repo_root()
    index_dir = root / "_ctx" / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    # Get all worktrees from git
    worktrees = get_worktrees_from_git(root)

    # Load all WOs
    work_orders = []
    errors = []

    for state_dir in ["pending", "running", "done", "failed"]:
        state_path = root / "_ctx" / "jobs" / state_dir
        if not state_path.exists():
            continue

        for wo_file in state_path.glob("WO-*.yaml"):
            try:
                entry = build_wo_index(wo_file, root, worktrees)
                work_orders.append(entry)
            except Exception as e:
                errors.append(f"Failed to load {wo_file.name}: {e}")

    # Build index
    index = {
        "version": 1,
        "schema": "trifecta.sidecar.wo_index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "git_head_sha_repo_root": get_git_head_sha(root),
        "work_orders": work_orders,
        "errors": errors
    }

    # Atomic write
    tmp_file = index_dir / "wo_worktrees.json.tmp"
    final_file = index_dir / "wo_worktrees.json"

    with open(tmp_file, "w") as f:
        json.dump(index, f, indent=2, default=str)

    tmp_file.rename(final_file)
    print(f"Index written to {final_file}")

    # Print summary
    print(f"  Work orders: {len(work_orders)}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors:
            print(f"    - {err}")


if __name__ == "__main__":
    main()
