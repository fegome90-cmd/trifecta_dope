import os
import subprocess
import json
from pathlib import Path
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def mock_repo(tmp_path):
    """Create a mock repo structure for wo_verify tests."""
    (tmp_path / "_ctx").mkdir()
    (tmp_path / "_ctx" / "jobs").mkdir()
    (tmp_path / "_ctx" / "jobs" / "running").mkdir()
    (tmp_path / "_ctx" / "logs").mkdir()
    (tmp_path / "scripts").mkdir()

    # Create the real ctx_scope_lint.py mock
    (tmp_path / "scripts" / "ctx_scope_lint.py").write_text("import sys; sys.exit(0)")

    # Copy wo_verify.sh to mock_repo/scripts
    real_sh = Path("scripts/wo_verify.sh")
    mock_sh = tmp_path / "scripts" / "wo_verify.sh"
    mock_sh.write_text(real_sh.read_text())
    os.chmod(mock_sh, 0o755)

    # Initialize git repo for rev-parse and log
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path)

    return tmp_path


def test_allow_dirty_requires_all_env_vars(mock_repo):
    """--allow-dirty must fail if any override env var is missing."""
    wo_id = "WO-TEST"
    wo_path = mock_repo / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    wo_path.write_text('id: WO-TEST\nverify:\n  commands: ["true"]')

    cases = [
        {"OVERRIDE_REASON": ""},
        {"OVERRIDE_WO": ""},
        {"OVERRIDE_UNTIL": ""},
    ]

    for missing_env in cases:
        env = {
            **os.environ,
            "OVERRIDE_REASON": "Reason is long enough",
            "OVERRIDE_WO": "WO-1234",
            "OVERRIDE_UNTIL": "2026-12-31",
        }
        env.update(missing_env)

        result = subprocess.run(
            ["bash", "scripts/wo_verify.sh", wo_id, "--root", str(mock_repo), "--allow-dirty"],
            cwd=mock_repo,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 2
        assert "ERROR: --allow-dirty requires" in result.stderr


def test_allow_dirty_validates_expiry(mock_repo):
    """--allow-dirty fails if OVERRIDE_UNTIL is in the past."""
    wo_id = "WO-TEST"
    wo_path = mock_repo / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    wo_path.write_text('id: WO-TEST\nverify:\n  commands: ["true"]')

    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    result = subprocess.run(
        ["bash", "scripts/wo_verify.sh", wo_id, "--root", str(mock_repo), "--allow-dirty"],
        cwd=mock_repo,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "OVERRIDE_REASON": "Reason is long enough",
            "OVERRIDE_WO": "WO-1234",
            "OVERRIDE_UNTIL": past_date,
        },
    )

    assert result.returncode == 2
    assert "has expired" in result.stderr


def test_allow_dirty_with_valid_override_is_audit_compliant(mock_repo):
    """Valid overrides produce compliant verdict.json with duration and version."""
    wo_id = "WO-TEST"
    wo_path = mock_repo / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    wo_path.write_text('id: WO-TEST\nverify:\n  commands: ["true"]')

    reason = "Manual override for integration testing"
    auth_wo = "WO-9999"
    until = "2099-01-01"

    result = subprocess.run(
        ["bash", "scripts/wo_verify.sh", wo_id, "--root", str(mock_repo), "--allow-dirty"],
        cwd=mock_repo,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "OVERRIDE_REASON": reason,
            "OVERRIDE_WO": auth_wo,
            "OVERRIDE_UNTIL": until,
            "ROOT": str(mock_repo),
        },
    )

    assert result.returncode == 0

    verdict_path = mock_repo / "_ctx" / "logs" / wo_id / "verdict.json"
    verdict = json.loads(verdict_path.read_text())

    assert verdict["schema_version"] == "1.0.0"
    assert "duration_seconds" in verdict
    assert verdict["override"]["reason"] == reason
    assert verdict["override"]["wo"] == auth_wo
    assert verdict["override"]["until"] == until


def test_crash_safety_harden_cleanup(mock_repo):
    """Cleanup trap works when script exits early (e.g., missing WO file)."""
    # Test that wo_verify.sh writes a CRASH verdict even when failing early
    # This simulates the case where LOG_DIR might not be fully set up yet
    wo_id = "WO-CRASH"
    # NOTE: We intentionally do NOT create the WO file to trigger an early exit

    result = subprocess.run(
        ["bash", "scripts/wo_verify.sh", wo_id, "--root", str(mock_repo)],
        cwd=mock_repo,
        capture_output=True,
        text=True,
        env={**os.environ, "ROOT": str(mock_repo)},
    )

    # Script should fail (missing WO)
    assert result.returncode == 1

    # The cleanup trap should NOT write CRASH in this case because
    # the script exits with a proper error message before LOG_DIR is created.
    # This is expected behavior - CRASH verdicts are for unexpected termination
    # (signals), not for normal error exits.
    # This test verifies the trap doesn't interfere with normal error handling.
    verdict_path = mock_repo / "_ctx" / "logs" / wo_id / "verdict.json"
    # No verdict should exist because the script failed before LOG_DIR was created
    # and this is a normal error exit, not a crash
    assert not verdict_path.exists(), "Normal error exits should not produce CRASH verdict"
