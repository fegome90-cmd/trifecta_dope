#!/usr/bin/env python3
"""
Integration tests for WO split-brain detection and integrity gates.

These tests verify the wo_audit.py forensic auditor correctly detects:
- split_brain (P0): WO in multiple state directories
- fail_but_running (P0): FAIL verdict but still in running/

These are P0 findings that should trigger CI failure.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def wo_repo(tmp_path):
    """Create a minimal WO repo structure for testing."""
    jobs_dir = tmp_path / "_ctx" / "jobs"
    for state in ("pending", "running", "done", "failed"):
        (jobs_dir / state).mkdir(parents=True)

    logs_dir = tmp_path / "_ctx" / "logs"
    logs_dir.mkdir(parents=True)

    backlog_dir = tmp_path / "_ctx" / "backlog"
    backlog_dir.mkdir(parents=True)
    (backlog_dir / "backlog.yaml").write_text("epics: {}\n")

    # Create minimal .git for worktree commands
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")

    return tmp_path


def wo_yaml_content(wo_id: str, status: str = "pending") -> str:
    """Generate minimal WO YAML content."""
    return f"""version: 1
id: {wo_id}
epic_id: E-TEST
title: Test WO for {wo_id}
priority: P1
status: {status}
scope:
  allow: ["src/"]
  deny: ["_ctx/"]
verify:
  commands: ["echo 'test'"]
"""


def test_wo_audit_detects_split_brain(wo_repo):
    """
    P0 CRITICAL: wo_audit.py MUST detect split-brain state.

    Split-brain = WO YAML exists in multiple state directories simultaneously.
    This is a P0 finding that should cause CI failure.
    """
    # Create WO in BOTH running/ AND done/ (split-brain)
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    done_dir = wo_repo / "_ctx" / "jobs" / "done"

    (running_dir / "WO-TEST1.yaml").write_text(wo_yaml_content("WO-TEST1", "running"))
    (done_dir / "WO-TEST1.yaml").write_text(wo_yaml_content("WO-TEST1", "done"))

    # Run audit
    out_path = wo_repo / "audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.wo_audit",
            "--root",
            str(wo_repo),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    # Parse audit result
    assert out_path.exists(), f"Audit output not created: {result.stderr}"
    audit = json.loads(out_path.read_text())

    # VERIFY split_brain detected
    split_brain_findings = [
        f for f in audit.get("findings", []) if f.get("code") == "split_brain"
    ]
    assert len(split_brain_findings) >= 1, (
        f"Expected split_brain finding for WO-TEST1. "
        f"Findings: {audit.get('findings', [])}"
    )
    assert split_brain_findings[0]["wo_id"] == "WO-TEST1"
    assert "running" in split_brain_findings[0]["states"]
    assert "done" in split_brain_findings[0]["states"]


def test_wo_audit_clean_state_no_p0(wo_repo):
    """
    Verify wo_audit.py returns 0 P0 findings with clean state.
    """
    pending_dir = wo_repo / "_ctx" / "jobs" / "pending"
    (pending_dir / "WO-CLEAN.yaml").write_text(wo_yaml_content("WO-CLEAN", "pending"))

    out_path = wo_repo / "audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.wo_audit",
            "--root",
            str(wo_repo),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    audit = json.loads(out_path.read_text())
    p0_count = audit.get("summary", {}).get("by_severity", {}).get("P0", 0)

    assert p0_count == 0, f"Expected 0 P0 findings in clean state, got {p0_count}"


def test_wo_audit_detects_fail_but_running(wo_repo):
    """
    P0 CRITICAL: wo_audit.py MUST detect FAIL verdict but still in running/.

    This indicates a transactional failure where the WO failed but wasn't
    properly transitioned to failed/ state.
    """
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    logs_dir = wo_repo / "_ctx" / "logs"

    # Create WO in running/
    (running_dir / "WO-FAILTEST.yaml").write_text(wo_yaml_content("WO-FAILTEST", "running"))

    # Create FAIL verdict in logs
    wo_logs = logs_dir / "WO-FAILTEST"
    wo_logs.mkdir()
    verdict = {
        "status": "FAIL",
        "wo_id": "WO-FAILTEST",
        "failure_stage": "verification",
        "finished_at": "2026-02-23T12:00:00Z",
    }
    (wo_logs / "verdict.json").write_text(json.dumps(verdict))

    out_path = wo_repo / "audit.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.wo_audit",
            "--root",
            str(wo_repo),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    audit = json.loads(out_path.read_text())

    # VERIFY fail_but_running detected
    fail_findings = [
        f for f in audit.get("findings", []) if f.get("code") == "fail_but_running"
    ]
    assert len(fail_findings) >= 1, (
        f"Expected fail_but_running finding for WO-FAILTEST. "
        f"Findings: {audit.get('findings', [])}"
    )
    assert fail_findings[0]["wo_id"] == "WO-FAILTEST"


def test_wo_audit_fail_on_flag(wo_repo):
    """
    Verify --fail-on flag causes exit 1 when specified finding code is detected.
    """
    # Create split-brain
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    done_dir = wo_repo / "_ctx" / "jobs" / "done"
    (running_dir / "WO-SPLIT.yaml").write_text(wo_yaml_content("WO-SPLIT", "running"))
    (done_dir / "WO-SPLIT.yaml").write_text(wo_yaml_content("WO-SPLIT", "done"))

    out_path = wo_repo / "audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.wo_audit",
            "--root",
            str(wo_repo),
            "--out",
            str(out_path),
            "--fail-on",
            "split_brain",
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    # Should exit 1 because split_brain was found
    assert result.returncode == 1, (
        f"Expected exit 1 with --fail-on split_brain, got {result.returncode}. "
        f"stdout: {result.stdout}"
    )


def test_make_wo_integrity_target(wo_repo):
    """
    Verify 'make wo-integrity' runs audit with correct fail-on codes.
    """
    # This test validates the Makefile target, not wo_audit directly
    # We verify by checking the Makefile has the correct invocation
    makefile_path = Path(__file__).parent.parent.parent / "Makefile"
    if not makefile_path.exists():
        pytest.skip("Makefile not found")

    makefile_content = makefile_path.read_text()

    # Check for wo-integrity target with fail-on for P0 findings
    assert "wo-integrity" in makefile_content, "Missing wo-integrity target in Makefile"
    assert "split_brain" in makefile_content or "fail_but_running" in makefile_content, (
        "wo-integrity should fail on P0 findings (split_brain, fail_but_running)"
    )
