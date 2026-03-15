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
    # Capture all log levels
    caplog.set_level("DEBUG")

    # Setup mock repo root
    repo_ctx = tmp_path
    (repo_ctx / "_ctx" / "jobs" / "pending").mkdir(parents=True)
    (repo_ctx / "_ctx" / "jobs" / "running").mkdir(parents=True)
    (repo_ctx / "_ctx" / "backlog").mkdir(parents=True)

    # Create backlog with epic for validation
    backlog = repo_ctx / "_ctx" / "backlog" / "backlog.yaml"
    backlog.write_text("""epics:
  - id: E-0001
    title: Test Epic
    status: active
""")

    wo_id = "WO-0050"
    pending_wo = repo_ctx / "_ctx" / "jobs" / "pending" / f"{wo_id}.yaml"
    pending_wo.write_text(f"""id: {wo_id}
status: pending
version: 1
epic_id: E-0001
execution:
  engine: trifecta
  segment: .
  required_flow:
    - session.append:intent
    - ctx.sync
    - ctx.search
    - ctx.get
    - session.append:result
""")

    monkeypatch.setattr("sys.argv", ["ctx_wo_take.py", wo_id, "--root", str(repo_ctx)])

    # Simulate a crash inside create_worktree by patching it to raise an exception
    def crashing_create_worktree(*args, **kwargs):
        raise RuntimeError("Simulated system crash during worktree creation")

    monkeypatch.setattr(ctx_wo_take, "create_worktree", crashing_create_worktree)
    monkeypatch.setattr(ctx_wo_take, "validate_dependencies_using_domain", lambda w, r: (True, None))

    # Mock validate_wo_immediately to pass validation (it calls external lint script)
    monkeypatch.setattr(ctx_wo_take, "validate_wo_immediately", lambda r, w, j: (True, []))

    # Mock load_schema to avoid needing actual schema file in temp path
    monkeypatch.setattr(ctx_wo_take, "load_schema", lambda r, n: {})

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
