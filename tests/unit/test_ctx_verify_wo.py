#!/usr/bin/env python3
"""
Unit tests for ctx_verify_wo.py - Scoped WO Verification.

HARD RULE: ctx_verify_wo.py MUST:
1. Search WO in (running, pending, failed, done) - all 4 states
2. FAIL (exit 2) if WO appears in >1 state (split-brain)
3. FAIL (exit 2) if WO has no verify.commands defined (no fallback PASS)
4. Return exit 0 only if ALL commands pass
5. Return exit 1 if any command fails
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def wo_repo(tmp_path):
    """Create minimal WO repo structure."""
    jobs_dir = tmp_path / "_ctx" / "jobs"
    for state in ("pending", "running", "done", "failed"):
        (jobs_dir / state).mkdir(parents=True)

    logs_dir = tmp_path / "_ctx" / "logs"
    logs_dir.mkdir(parents=True)

    return tmp_path


def wo_yaml_with_commands(wo_id: str, commands: list[str]) -> str:
    """Generate WO YAML with specific verify.commands."""
    # Format commands as proper YAML list
    commands_lines = "\n".join(f"    - {cmd}" for cmd in commands)
    return f"""version: 1
id: {wo_id}
epic_id: E-TEST
title: Test WO
priority: P1
status: running
scope:
  allow:
    - "src/"
  deny:
    - "_ctx/"
verify:
  commands:
{commands_lines}
"""


def wo_yaml_no_commands(wo_id: str) -> str:
    """Generate WO YAML WITHOUT verify.commands."""
    return f"""version: 1
id: {wo_id}
epic_id: E-TEST
title: Test WO
priority: P1
status: running
scope:
  allow: ["src/"]
  deny: ["_ctx/"]
verify: {{}}
"""


# === UNIT TESTS ===


def test_load_wo_yaml_finds_running(wo_repo):
    """ctx_verify_wo.py must find WO in running/ state."""
    from ctx_verify_wo import load_wo_yaml

    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    (running_dir / "WO-UNIT1.yaml").write_text(wo_yaml_with_commands("WO-UNIT1", ["echo test"]))

    result = load_wo_yaml(wo_repo, "WO-UNIT1")
    assert result is not None
    assert result["id"] == "WO-UNIT1"


def test_load_wo_yaml_finds_pending(wo_repo):
    """ctx_verify_wo.py must find WO in pending/ state."""
    from ctx_verify_wo import load_wo_yaml

    pending_dir = wo_repo / "_ctx" / "jobs" / "pending"
    (pending_dir / "WO-UNIT2.yaml").write_text(wo_yaml_with_commands("WO-UNIT2", ["echo test"]))

    result = load_wo_yaml(wo_repo, "WO-UNIT2")
    assert result is not None
    assert result["id"] == "WO-UNIT2"


def test_load_wo_yaml_finds_done(wo_repo):
    """ctx_verify_wo.py must find WO in done/ state."""
    from ctx_verify_wo import load_wo_yaml

    done_dir = wo_repo / "_ctx" / "jobs" / "done"
    (done_dir / "WO-UNIT3.yaml").write_text(wo_yaml_with_commands("WO-UNIT3", ["echo test"]))

    result = load_wo_yaml(wo_repo, "WO-UNIT3")
    assert result is not None


def test_load_wo_yaml_finds_failed(wo_repo):
    """ctx_verify_wo.py must find WO in failed/ state."""
    from ctx_verify_wo import load_wo_yaml

    failed_dir = wo_repo / "_ctx" / "jobs" / "failed"
    (failed_dir / "WO-UNIT4.yaml").write_text(wo_yaml_with_commands("WO-UNIT4", ["echo test"]))

    result = load_wo_yaml(wo_repo, "WO-UNIT4")
    assert result is not None


def test_load_wo_yaml_not_found_returns_none(wo_repo):
    """ctx_verify_wo.py must return None for non-existent WO."""
    from ctx_verify_wo import load_wo_yaml

    result = load_wo_yaml(wo_repo, "WO-NONEXISTENT")
    assert result is None


def test_detect_split_brain(wo_repo):
    """ctx_verify_wo.py must FAIL (exit 2) if WO in multiple states."""
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    done_dir = wo_repo / "_ctx" / "jobs" / "done"

    (running_dir / "WO-SPLIT.yaml").write_text(wo_yaml_with_commands("WO-SPLIT", ["echo test"]))
    (done_dir / "WO-SPLIT.yaml").write_text(wo_yaml_with_commands("WO-SPLIT", ["echo test"]))

    # Run ctx_verify_wo.py
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ctx_verify_wo",
            "WO-SPLIT",
            "--root",
            str(wo_repo),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    # MUST exit 2 for split-brain
    assert result.returncode == 2, (
        f"Expected exit 2 for split-brain, got {result.returncode}. "
        f"stdout: {result.stdout}, stderr: {result.stderr}"
    )
    assert "split" in result.stdout.lower() or "split" in result.stderr.lower()


def test_no_verify_commands_fails(wo_repo):
    """HARD RULE: No verify.commands -> FAIL (exit 2), no fallback PASS."""
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    (running_dir / "WO-NO-CMDS.yaml").write_text(wo_yaml_no_commands("WO-NO-CMDS"))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ctx_verify_wo",
            "WO-NO-CMDS",
            "--root",
            str(wo_repo),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    # MUST exit 2 for missing verify.commands
    assert result.returncode == 2, (
        f"Expected exit 2 for missing verify.commands, got {result.returncode}. "
        f"stdout: {result.stdout}"
    )
    assert "verify.commands" in result.stdout.lower() or "verify.commands" in result.stderr.lower()


def test_commands_pass_returns_0(wo_repo):
    """All commands pass -> exit 0."""
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    (running_dir / "WO-PASS.yaml").write_text(
        wo_yaml_with_commands("WO-PASS", ["echo 'test 1'", "echo 'test 2'"])
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ctx_verify_wo",
            "WO-PASS",
            "--root",
            str(wo_repo),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    assert result.returncode == 0, (
        f"Expected exit 0 for passing commands, got {result.returncode}. "
        f"stdout: {result.stdout}"
    )
    assert "PASS" in result.stdout


def test_command_fail_returns_1(wo_repo):
    """Any command fails -> exit 1."""
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    (running_dir / "WO-FAIL.yaml").write_text(
        wo_yaml_with_commands("WO-FAIL", ["echo 'pass'", "exit 1"])
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ctx_verify_wo",
            "WO-FAIL",
            "--root",
            str(wo_repo),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    assert result.returncode == 1, (
        f"Expected exit 1 for failing command, got {result.returncode}. "
        f"stdout: {result.stdout}"
    )
    assert "FAIL" in result.stdout


def test_json_output(wo_repo):
    """--json flag produces valid JSON report."""
    running_dir = wo_repo / "_ctx" / "jobs" / "running"
    (running_dir / "WO-JSON.yaml").write_text(
        wo_yaml_with_commands("WO-JSON", ["echo 'test'"])
    )

    json_path = wo_repo / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ctx_verify_wo",
            "WO-JSON",
            "--root",
            str(wo_repo),
            "--json",
            str(json_path),
        ],
        capture_output=True,
        text=True,
        cwd=wo_repo,
    )

    assert json_path.exists(), "JSON report not created"
    report = json.loads(json_path.read_text())
    assert report["wo_id"] == "WO-JSON"
    assert report["status"] == "PASS"
    assert report["commands_run"] == 1
    assert report["commands_passed"] == 1
