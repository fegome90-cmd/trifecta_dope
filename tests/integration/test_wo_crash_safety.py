import os
import pytest
from pathlib import Path

# Imported modules
from scripts.ctx_wo_take import main as take_main
from scripts.helpers import get_lock_path
from scripts import ctx_wo_take


def test_wo_crash_safety_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Setup mock repo root
    repo_ctx = tmp_path
    (repo_ctx / "_ctx" / "jobs" / "pending").mkdir(parents=True)
    (repo_ctx / "_ctx" / "jobs" / "running").mkdir(parents=True)

    wo_id = "WO-0050"
    pending_wo = repo_ctx / "_ctx" / "jobs" / "pending" / f"{wo_id}.yaml"
    pending_wo.write_text(f"id: {wo_id}\nstatus: pending\nversion: 1\nepic_id: E-0001\n")

    monkeypatch.setattr("sys.argv", ["ctx_wo_take.py", wo_id, "--root", str(repo_ctx)])

    # Simulate a crash inside create_worktree by patching it to raise an exception
    def crashing_create_worktree(*args, **kwargs):
        raise RuntimeError("Simulated system crash during worktree creation")

    monkeypatch.setattr(ctx_wo_take, "create_worktree", crashing_create_worktree)
    monkeypatch.setattr(ctx_wo_take, "validate_dependencies", lambda w: (True, ""))

    # We must patch lint_run so it doesn't fail pre-flight
    monkeypatch.setattr("scripts.ctx_wo_take.lint_run", lambda r, strict, wo_id: [])

    # The previous code had a bug where result was an int (or None). We use caplog for checking rolling back.
    exit_code = take_main()

    # ensure it failed cleanly
    assert exit_code == 1

    # verify the rollback log message
    log_text = caplog.text.lower()
    assert (
        getattr(log_text, "find", lambda x: -1)("rollback") != -1
        or "rollback" in log_text
        or "rolled back" in log_text
    )

    # Invariants checks:
    # 1. Lock must have been removed
    lock_path = get_lock_path(repo_ctx, wo_id)
    assert not lock_path.exists()

    # 2. WO Must be back in pending directory
    assert pending_wo.exists()
    assert pending_wo.parent.name == "pending"

    # 3. Not in running
    running_wo = repo_ctx / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    assert not running_wo.exists()
