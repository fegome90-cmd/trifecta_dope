from pathlib import Path
import json
import os
import signal
import subprocess
import time

import pytest
import yaml


# Get the actual repo root (where this test file lives)
REPO_ROOT = Path(__file__).parent.parent.parent


def _write_test_wo(wo_id: str, payload: dict) -> Path:
    """Write a test WO to running/ for verification."""
    wo_dir = REPO_ROOT / "_ctx" / "jobs" / "running"
    wo_dir.mkdir(parents=True, exist_ok=True)
    wo_path = wo_dir / f"{wo_id}.yaml"
    wo_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return wo_path


def _cleanup_test_wo(wo_id: str):
    """Clean up test WO and its logs."""
    wo_path = REPO_ROOT / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    if wo_path.exists():
        wo_path.unlink()

    log_dir = REPO_ROOT / "_ctx" / "logs" / wo_id
    if log_dir.exists():
        import shutil

        shutil.rmtree(log_dir)


def _run_wo_verify(
    wo_id: str,
    allow_dirty: bool = False,
    env: dict | None = None,
    kill_after_ms: int | None = None,
) -> subprocess.CompletedProcess:
    """Run wo_verify.sh with optional kill signal after delay."""
    cmd = ["bash", "scripts/wo_verify.sh", wo_id, "--root", "."]
    if allow_dirty:
        cmd.append("--allow-dirty")

    # Default override env vars for --allow-dirty (required by wo_verify.sh)
    default_override_env = {}
    if allow_dirty:
        default_override_env = {
            "OVERRIDE_REASON": f"Test override for {wo_id}",
            "OVERRIDE_WO": "WO-0000",  # Valid format: WO-[0-9]+
            "OVERRIDE_UNTIL": "2099-12-31",
        }

    merged_env = {**os.environ, **default_override_env, **(env or {})}

    if kill_after_ms is None:
        return subprocess.run(cmd, capture_output=True, text=True, env=merged_env, cwd=REPO_ROOT)

    # Start process and kill it after delay
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=merged_env,
        cwd=REPO_ROOT,
    )
    time.sleep(kill_after_ms / 1000.0)
    proc.send_signal(signal.SIGTERM)
    stdout, stderr = proc.communicate()
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


# =============================================================================
# P1.2: Trap / Crash Safety Tests
# =============================================================================


def test_wo_verify_writes_verdict_on_normal_pass():
    """P1.2: verdict.json must be written on successful verification."""
    wo_id = "WO-TEST-PASS"

    try:
        _write_test_wo(
            wo_id,
            {
                "id": wo_id,
                "scope": {
                    "allow": ["*"],
                    "override": True,
                    "override_reason": "Test case for verdict writing",
                    "override_expires": "2099-12-31",
                },
                "verify": {"commands": ["echo 'test passed'"]},
            },
        )

        result = _run_wo_verify(wo_id, allow_dirty=True)
        assert result.returncode == 0, f"Expected success: {result.stderr}"

        # Verify verdict.json exists and has correct status
        verdict_file = REPO_ROOT / "_ctx" / "logs" / wo_id / "verdict.json"
        assert verdict_file.exists(), "verdict.json must exist after successful verification"

        verdict = json.loads(verdict_file.read_text())
        assert verdict["status"] == "PASS"
        assert verdict["wo_id"] == wo_id
        assert "git_commit" in verdict
        assert "started_at" in verdict
        assert "finished_at" in verdict
    finally:
        _cleanup_test_wo(wo_id)


def test_wo_verify_writes_verdict_on_normal_fail():
    """P1.2: verdict.json must be written on failed verification."""
    wo_id = "WO-TEST-FAIL"

    try:
        _write_test_wo(
            wo_id,
            {
                "id": wo_id,
                "scope": {
                    "allow": ["*"],
                    "override": True,
                    "override_reason": "Test case for verdict fail",
                    "override_expires": "2099-12-31",
                },
                "verify": {"commands": ["exit 1"]},  # Command that fails
            },
        )

        result = _run_wo_verify(wo_id, allow_dirty=True)
        assert result.returncode == 1

        # Verify verdict.json exists and has FAIL status
        verdict_file = REPO_ROOT / "_ctx" / "logs" / wo_id / "verdict.json"
        assert verdict_file.exists(), "verdict.json must exist even on failure"

        verdict = json.loads(verdict_file.read_text())
        assert verdict["status"] == "FAIL"
    finally:
        _cleanup_test_wo(wo_id)


def test_wo_verify_writes_crash_verdict_on_sigterm():
    """P1.2: Send SIGTERM to wo_verify.sh and verify CRASH verdict is written."""
    wo_id = "WO-TEST-CRASH"

    try:
        _write_test_wo(
            wo_id,
            {
                "id": wo_id,
                "scope": {
                    "allow": ["*"],
                    "override": True,
                    "override_reason": "Test case for crash trap",
                    "override_expires": "2099-12-31",
                },
                "verify": {"commands": ["sleep 10"]},  # Long-running command
            },
        )

        # Kill process after 200ms
        result = _run_wo_verify(wo_id, allow_dirty=True, kill_after_ms=200)

        # Process was killed, so non-zero exit
        assert result.returncode != 0

        # Verify CRASH verdict was written by trap
        verdict_file = REPO_ROOT / "_ctx" / "logs" / wo_id / "verdict.json"
        assert verdict_file.exists(), "verdict.json must exist even after SIGTERM"

        verdict = json.loads(verdict_file.read_text())
        assert verdict["status"] == "CRASH", f"Expected CRASH status, got {verdict['status']}"
        assert verdict["failure_stage"] == "unexpected_exit"
    finally:
        _cleanup_test_wo(wo_id)


def test_verdict_schema_validation_on_existing_verdict():
    """P1.2: Validate that schema matches actual verdict from wo_verify.sh."""
    wo_id = "WO-TEST-SCHEMA"

    try:
        _write_test_wo(
            wo_id,
            {
                "id": wo_id,
                "epic_id": "E-0001",
                "dod_id": "DOD-DEFAULT",
                "scope": {
                    "allow": ["*"],
                    "override": True,
                    "override_reason": "Test verdict schema validation",
                    "override_expires": "2099-12-31",
                },
                "verify": {"commands": ["echo 'schema test'"]},
            },
        )

        result = _run_wo_verify(wo_id, allow_dirty=True)
        assert result.returncode == 0, f"Expected success: {result.stderr}"

        verdict_file = REPO_ROOT / "_ctx" / "logs" / wo_id / "verdict.json"
        verdict = json.loads(verdict_file.read_text())

        # Validate required fields exist
        assert "wo_id" in verdict
        assert "status" in verdict
        assert "git_commit" in verdict
        assert "started_at" in verdict
        assert "finished_at" in verdict
        assert "commands" in verdict

        # Validate types
        assert isinstance(verdict["commands"], list)
        assert verdict["status"] in ["PASS", "FAIL", "CRASH"]
    finally:
        _cleanup_test_wo(wo_id)


# =============================================================================
# P1.3: Override Accountability Tests (will be activated in P1.3)
# =============================================================================
# These tests are placeholders for P1.3 and will be updated
# when override validation is implemented.
