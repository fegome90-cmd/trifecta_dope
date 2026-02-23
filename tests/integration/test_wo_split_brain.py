"""Anti-split-brain test - guarantees one WO = one state file."""
from __future__ import annotations

from pathlib import Path

import pytest


def get_wo_state_files(jobs_dir: Path) -> dict[str, list[Path]]:
    """Find all WO YAML files and group by WO ID."""
    wo_files: dict[str, list[Path]] = {}
    for state in ("pending", "running", "done", "failed"):
        state_dir = jobs_dir / state
        if not state_dir.exists():
            continue
        for yaml_file in state_dir.glob("WO-*.yaml"):
            wo_id = yaml_file.stem
            if wo_id not in wo_files:
                wo_files[wo_id] = []
            wo_files[wo_id].append(yaml_file)
    return wo_files


def test_no_split_brain() -> None:
    """Invariant: each WO exists in exactly ONE state directory."""
    # Find repo root
    root = Path(__file__).resolve().parent.parent.parent
    jobs_dir = root / "_ctx" / "jobs"

    wo_files = get_wo_state_files(jobs_dir)

    duplicates = {
        wo_id: paths for wo_id, paths in wo_files.items() if len(paths) > 1
    }

    if duplicates:
        msg_lines = ["SPLIT-BRAIN DETECTED:"]
        for wo_id, paths in duplicates.items():
            paths_str = ", ".join(str(p.relative_to(root)) for p in paths)
            msg_lines.append(f"  {wo_id}: {paths_str}")
        pytest.fail("\n".join(msg_lines))


def test_no_orphan_locks() -> None:
    """Invariant: every lock has a corresponding running YAML."""
    root = Path(__file__).resolve().parent.parent.parent
    running_dir = root / "_ctx" / "jobs" / "running"

    if not running_dir.exists():
        return  # No running dir, test passes

    locks = {f.stem for f in running_dir.glob("*.lock")}
    yamls = {f.stem for f in running_dir.glob("WO-*.yaml")}

    orphan_locks = locks - yamls

    if orphan_locks:
        pytest.fail(f"ORPHAN LOCKS: {orphan_locks}")


def test_no_running_without_lock() -> None:
    """Invariant: every running WO has a lock file."""
    root = Path(__file__).resolve().parent.parent.parent
    running_dir = root / "_ctx" / "jobs" / "running"

    if not running_dir.exists():
        return

    yamls = {f.stem for f in running_dir.glob("WO-*.yaml")}
    locks = {f.stem for f in running_dir.glob("*.lock")}

    missing_locks = yamls - locks

    if missing_locks:
        pytest.fail(f"RUNNING WITHOUT LOCK: {missing_locks}")
