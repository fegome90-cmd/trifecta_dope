import subprocess


def test_reconcile_detects_running_without_lock():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WITHOUT_LOCK" in result.stdout


def test_reconcile_detects_lock_without_running_wo():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "lock_without_running_wo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "LOCK_WITHOUT_RUNNING_WO" in result.stdout


def test_reconcile_detects_running_wo_without_worktree():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_wo_without_worktree"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WO_WITHOUT_WORKTREE" in result.stdout


def test_reconcile_apply_regenerates_lock_only_with_apply_flag():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "would_create_lock" in result.stdout


def test_reconcile_never_moves_states_without_force():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_wo_without_worktree", "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --force" in result.stdout


def test_reconcile_detects_duplicate_wo_id_across_states():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "duplicate_wo_id_across_states"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "DUPLICATE_WO_ID" in result.stdout


def test_reconcile_detects_invalid_schema_and_refuses_apply():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "WO_INVALID_SCHEMA" in result.stdout

    result_apply = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema", "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result_apply.returncode != 0
    assert "apply refused" in result_apply.stdout
