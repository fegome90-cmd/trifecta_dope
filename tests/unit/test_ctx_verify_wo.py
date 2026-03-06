"""Unit tests for ctx_verify_wo.py contract."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def test_returns_1_when_wo_not_found(tmp_path: Path) -> None:
    """Should return 1 when WO YAML doesn't exist."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ctx_verify_wo.py",
            "WO-9999",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


def test_returns_0_when_no_verify_commands(tmp_path: Path) -> None:
    """Should return 0 when WO has no verify.commands."""
    # Create minimal WO structure
    jobs_dir = tmp_path / "_ctx" / "jobs" / "running"
    jobs_dir.mkdir(parents=True)
    wo_yaml = jobs_dir / "WO-TEST.yaml"
    wo_yaml.write_text("id: WO-TEST\nverify:\n  commands: []\n")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ctx_verify_wo.py",
            "WO-TEST",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No verify.commands" in result.stdout


def test_returns_1_when_command_fails(tmp_path: Path) -> None:
    """Should return 1 when a verify command fails."""
    jobs_dir = tmp_path / "_ctx" / "jobs" / "running"
    jobs_dir.mkdir(parents=True)
    wo_yaml = jobs_dir / "WO-TEST.yaml"
    wo_yaml.write_text(
        """
id: WO-TEST
verify:
  commands:
    - exit 1
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ctx_verify_wo.py",
            "WO-TEST",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "FAILED" in result.stdout


def test_returns_0_when_command_succeeds(tmp_path: Path) -> None:
    """Should return 0 when all verify commands succeed."""
    jobs_dir = tmp_path / "_ctx" / "jobs" / "running"
    jobs_dir.mkdir(parents=True)
    wo_yaml = jobs_dir / "WO-TEST.yaml"
    wo_yaml.write_text(
        """
id: WO-TEST
verify:
  commands:
    - echo "pass"
    - echo "also pass"
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ctx_verify_wo.py",
            "WO-TEST",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "ALL VERIFIED" in result.stdout
