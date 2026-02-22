import pytest
from pathlib import Path
from scripts.ctx_wo_take import main as take_main
from scripts.helpers import create_lock


def test_wo_take_concurrency_clean_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo_ctx = tmp_path
    (repo_ctx / "_ctx" / "jobs" / "pending").mkdir(parents=True)
    (repo_ctx / "_ctx" / "jobs" / "running").mkdir(parents=True)

    wo_id = "WO-0050"

    # Process A has supposedly acquired the lock and moved the file
    lock_path = repo_ctx / "_ctx" / "jobs" / "running" / f"{wo_id}.lock"

    # Create valid lock holding our PID so it isn't seen as orphaned
    assert create_lock(lock_path, wo_id) is True, "Failed to mock lock"

    # Process A also moved the WO to running
    running_wo = repo_ctx / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    running_wo.write_text(f"id: {wo_id}\nstatus: running\n")

    monkeypatch.setattr("sys.argv", ["ctx_wo_take.py", wo_id, "--root", str(repo_ctx)])

    # Patch linter so Process B passes preflight
    monkeypatch.setattr("scripts.ctx_wo_take.lint_run", lambda r, strict, wo_id: [])
    # Process B runs:
    # It should try to acquire the lock, fail (since Process A's lock is valid),
    # and exit cleanly with 1.
    result = take_main()
    assert result == 1

    # INVARIANTS CHECK
    # 1 lock remains
    locks = list((repo_ctx / "_ctx" / "jobs" / "running").glob("*.lock"))
    assert len(locks) == 1
    assert locks[0].name == f"{wo_id}.lock"

    # 1 active running YAML remains
    running_yamls = list((repo_ctx / "_ctx" / "jobs" / "running").glob("*.yaml"))
    assert len(running_yamls) == 1
    assert running_yamls[0].name == f"{wo_id}.yaml"
