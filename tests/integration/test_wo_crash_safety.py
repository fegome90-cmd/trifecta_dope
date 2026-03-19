import os
import subprocess
from pathlib import Path

import pytest
import yaml

# Imported modules
from scripts.ctx_wo_take import main as take_main
from scripts import ctx_wo_finish
from scripts.ctx_wo_finish import finish_wo_transaction
from scripts.helpers import get_lock_path
from scripts import ctx_wo_take
from scripts.wo_audit import audit
from src.domain.result import Err


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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_checked(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _init_finish_repo(tmp_path: Path, *, merged: bool) -> tuple[Path, Path, Path]:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()

    (runtime_root / ".gitignore").write_text(".worktrees/\n")
    (runtime_root / "README.md").write_text("fixture\n")

    running_dir = runtime_root / "_ctx" / "jobs" / "running"
    running_dir.mkdir(parents=True)
    dod_dir = runtime_root / "_ctx" / "dod"
    dod_dir.mkdir(parents=True)

    (dod_dir / "DOD-TEST.yaml").write_text(
        "dod:\n"
        "  - id: DOD-TEST\n"
        '    name: "Test DoD"\n'
        "    requirements: []\n"
    )
    (running_dir / "WO-TEST.yaml").write_text(
        "version: 1\n"
        "id: WO-TEST\n"
        "epic_id: E-TEST\n"
        'title: "Test WO"\n'
        "priority: P1\n"
        "status: running\n"
        "owner: tester\n"
        "dod_id: DOD-TEST\n"
        'x_objective: "Exercise closeout side effects"\n'
        "branch: feat/wo-WO-TEST\n"
        "worktree: .worktrees/WO-TEST\n"
    )

    _run_checked(["git", "init", "-b", "main"], cwd=runtime_root)
    _run_checked(["git", "config", "user.email", "test@example.com"], cwd=runtime_root)
    _run_checked(["git", "config", "user.name", "Test User"], cwd=runtime_root)
    _run_checked(["git", "add", "."], cwd=runtime_root)
    _run_checked(["git", "commit", "-m", "init runtime fixture"], cwd=runtime_root)

    official_worktree = runtime_root / ".worktrees" / "WO-TEST"
    _run_checked(
        ["git", "worktree", "add", str(official_worktree), "-b", "feat/wo-WO-TEST"],
        cwd=runtime_root,
    )
    (official_worktree / "feature.txt").write_text("change\n")
    _run_checked(["git", "add", "feature.txt"], cwd=official_worktree)
    _run_checked(["git", "commit", "-m", "feat: add change"], cwd=official_worktree)

    if merged:
        _run_checked(
            ["git", "merge", "--no-ff", "feat/wo-WO-TEST", "-m", "merge feature"],
            cwd=runtime_root,
        )

    preserved_baseline = runtime_root.parent / "wo-test-baseline"
    return runtime_root, official_worktree, preserved_baseline


def test_finish_closeout_remove_runs_for_merged_branch(tmp_path: Path) -> None:
    runtime_root, official_worktree, _ = _init_finish_repo(tmp_path, merged=True)

    result = subprocess.run(
        [
            "python",
            "scripts/ctx_wo_finish.py",
            "WO-TEST",
            "--root",
            str(official_worktree),
            "--skip-dod",
            "--skip-verification",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=_repo_root(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not official_worktree.exists()
    done_yaml = runtime_root / "_ctx" / "jobs" / "done" / "WO-TEST.yaml"
    done_data = yaml.safe_load(done_yaml.read_text())
    assert done_data["closeout"]["action"] == "cleanup_official_worktree"
    assert done_data["closeout"]["resulting_path"] is None


def test_finish_closeout_preserve_move_runs_for_unmerged_branch(tmp_path: Path) -> None:
    runtime_root, official_worktree, preserved_baseline = _init_finish_repo(tmp_path, merged=False)

    result = subprocess.run(
        [
            "python",
            "scripts/ctx_wo_finish.py",
            "WO-TEST",
            "--root",
            str(official_worktree),
            "--skip-dod",
            "--skip-verification",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=_repo_root(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not official_worktree.exists()
    assert preserved_baseline.exists()
    done_yaml = runtime_root / "_ctx" / "jobs" / "done" / "WO-TEST.yaml"
    done_data = yaml.safe_load(done_yaml.read_text())
    assert done_data["closeout"]["action"] == "preserve_baseline_checkout"
    assert done_data["closeout"]["resulting_path"] == str(preserved_baseline)


def test_finish_closeout_not_run_when_verification_fails(tmp_path: Path) -> None:
    runtime_root, official_worktree, preserved_baseline = _init_finish_repo(tmp_path, merged=False)

    result = subprocess.run(
        [
            "python",
            "scripts/ctx_wo_finish.py",
            "WO-TEST",
            "--root",
            str(official_worktree),
            "--skip-dod",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=_repo_root(),
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert official_worktree.exists()
    assert not preserved_baseline.exists()
    assert not (runtime_root / "_ctx" / "jobs" / "done" / "WO-TEST.yaml").exists()


def test_preserve_closeout_rollback_restores_running_state_without_partial_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_root, official_worktree, preserved_baseline = _init_finish_repo(tmp_path, merged=False)
    wo_id = "WO-TEST"
    running_dir = runtime_root / "_ctx" / "jobs" / "running"
    running_path = running_dir / f"{wo_id}.yaml"
    lock_path = running_dir / f"{wo_id}.lock"
    done_path = runtime_root / "_ctx" / "jobs" / "done" / f"{wo_id}.yaml"
    handoff_dir = runtime_root / "_ctx" / "handoff" / wo_id
    decision_path = handoff_dir / "decision.md"

    handoff_dir.mkdir(parents=True)
    lock_path.write_text('{"pid": 12345, "started_at": "2026-03-18T00:00:00Z"}')

    def fail_closeout(root: Path, closeout_policy: dict[str, object]):
        assert root == runtime_root
        assert closeout_policy["action"] == "preserve_baseline_checkout"
        assert decision_path.exists()
        return Err("simulated preserve closeout failure")

    monkeypatch.setattr("scripts.ctx_wo_finish.execute_closeout_action", fail_closeout)

    result = finish_wo_transaction(wo_id, runtime_root, "done")
    audit_result = audit(runtime_root)
    finding_codes = {
        finding["code"] for finding in audit_result["findings"] if finding.get("wo_id") == wo_id
    }

    assert result.is_err()
    assert running_path.exists()
    assert lock_path.exists()
    assert not done_path.exists()
    assert not decision_path.exists()
    assert official_worktree.exists()
    assert official_worktree.resolve() == (runtime_root / ".worktrees" / wo_id).resolve()
    assert not preserved_baseline.exists()
    assert "split_brain" not in finding_codes
    assert "running_without_lock" not in finding_codes
    assert "zombie_worktree" not in finding_codes


def test_finish_main_preserve_closeout_failure_restores_running_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_root, official_worktree, preserved_baseline = _init_finish_repo(tmp_path, merged=False)
    wo_id = "WO-TEST"
    running_dir = runtime_root / "_ctx" / "jobs" / "running"
    running_path = running_dir / f"{wo_id}.yaml"
    lock_path = running_dir / f"{wo_id}.lock"
    done_path = runtime_root / "_ctx" / "jobs" / "done" / f"{wo_id}.yaml"
    handoff_dir = runtime_root / "_ctx" / "handoff" / wo_id
    decision_path = handoff_dir / "decision.md"

    handoff_dir.mkdir(parents=True)
    lock_path.write_text('{"pid": 12345, "started_at": "2026-03-18T00:00:00Z"}')

    def fail_closeout(root: Path, closeout_policy: dict[str, object]):
        assert root == runtime_root
        assert closeout_policy["action"] == "preserve_baseline_checkout"
        assert decision_path.exists()
        return Err("simulated preserve closeout failure")

    monkeypatch.setattr("scripts.ctx_wo_finish.execute_closeout_action", fail_closeout)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ctx_wo_finish.py",
            wo_id,
            "--root",
            str(official_worktree),
            "--skip-dod",
            "--skip-verification",
        ],
    )

    exit_code = ctx_wo_finish.main()
    audit_result = audit(runtime_root)
    finding_codes = {
        finding["code"] for finding in audit_result["findings"] if finding.get("wo_id") == wo_id
    }

    assert exit_code == 1
    assert running_path.exists()
    assert lock_path.exists()
    assert not done_path.exists()
    assert not decision_path.exists()
    assert official_worktree.exists()
    assert official_worktree.resolve() == (runtime_root / ".worktrees" / wo_id).resolve()
    assert not preserved_baseline.exists()
    assert "split_brain" not in finding_codes
    assert "running_without_lock" not in finding_codes
    assert "zombie_worktree" not in finding_codes
