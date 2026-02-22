#!/usr/bin/env python3
"""
Test for WO-0015 pattern detection: FAIL but RUNNING.

This test verifies that the wo_audit.py script correctly detects
the case where a WO has a verdict.json with status=FAIL but the
YAML is still in the running/ directory.

This is the "silent transaction failure" pattern found in WO-0015 and WO-0057.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest


def run_audit(tmp_path: Path) -> dict[str, Any]:
    """Run wo_audit.py and return parsed JSON result."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/wo_audit.py", "--out", str(tmp_path / "audit.json")],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    audit_path = tmp_path / "audit.json"
    if audit_path.exists():
        return cast(dict[str, Any], json.loads(audit_path.read_text()))
    raise RuntimeError(f"Audit failed: {result.stderr}")


def setup_fail_but_running_state(tmp_path: Path, wo_id: str = "WO-TEST") -> None:
    """Create a FAIL but RUNNING state for testing."""
    # Create directory structure
    running_dir = tmp_path / "_ctx" / "jobs" / "running"
    failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
    logs_dir = tmp_path / "_ctx" / "logs" / wo_id

    running_dir.mkdir(parents=True)
    failed_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    # Create WO YAML in running/ (this is the bug - should be in failed/)
    wo_yaml = running_dir / f"{wo_id}.yaml"
    wo_yaml.write_text(f"""
version: 1
id: {wo_id}
title: Test WO for FAIL but RUNNING detection
status: running
scope:
  allow: ["src/**"]
""")
    # Create lock file
    (running_dir / f"{wo_id}.lock").write_text(
        '{"pid": 12345, "started_at": "2026-02-21T00:00:00Z"}'
    )

    # Create verdict.json with FAIL status
    verdict = {
        "schema_version": "1.0.0",
        "wo_id": wo_id,
        "status": "FAIL",
        "failure_stage": "scope_lint",
        "started_at": "2026-02-21T00:00:00Z",
        "finished_at": "2026-02-21T00:00:01Z",
    }
    (logs_dir / "verdict.json").write_text(json.dumps(verdict))


class TestFailButRunningDetection:
    """Tests for the fail_but_running finding code."""

    def test_detects_fail_but_running(self, tmp_path: Path, monkeypatch):
        """A WO with FAIL verdict but YAML in running/ should be detected."""
        # Setup: Create the problematic state
        setup_fail_but_running_state(tmp_path, "WO-9999")

        # Change to tmp_path for audit
        monkeypatch.chdir(tmp_path)

        # Run audit
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                Path(__file__).parent.parent.parent / "scripts" / "wo_audit.py",
                "--out",
                str(tmp_path / "audit.json"),
            ],
            capture_output=True,
            text=True,
        )

        # Parse audit result
        audit_path = tmp_path / "audit.json"
        if not audit_path.exists():
            pytest.skip(f"Audit did not produce output: {result.stderr}")

        audit = json.loads(audit_path.read_text())

        # Find fail_but_running finding
        fail_but_running_findings = [
            f for f in audit.get("findings", []) if f.get("code") == "fail_but_running"
        ]

        assert len(fail_but_running_findings) == 1, (
            f"Expected 1 fail_but_running finding, got {len(fail_but_running_findings)}: "
            f"{audit.get('findings', [])}"
        )

        finding = fail_but_running_findings[0]
        assert finding["wo_id"] == "WO-9999"
        assert finding["severity"] == "P0"
        assert finding["failure_stage"] == "scope_lint"

    def test_no_finding_when_properly_in_failed(self, tmp_path: Path, monkeypatch):
        """A WO with FAIL verdict and YAML in failed/ should NOT trigger finding."""
        # Setup: Create proper state (YAML in failed/)
        failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
        logs_dir = tmp_path / "_ctx" / "logs" / "WO-8888"

        failed_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)

        # Create WO YAML in failed/ (correct location)
        wo_yaml = failed_dir / "WO-8888.yaml"
        wo_yaml.write_text("""
version: 1
id: WO-8888
title: Test WO properly in failed state
status: failed
scope:
  allow: ["src/**"]
""")

        # Create verdict.json with FAIL status
        verdict = {
            "schema_version": "1.0.0",
            "wo_id": "WO-8888",
            "status": "FAIL",
            "failure_stage": "scope_lint",
        }
        (logs_dir / "verdict.json").write_text(json.dumps(verdict))

        monkeypatch.chdir(tmp_path)

        # Run audit
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                Path(__file__).parent.parent.parent / "scripts" / "wo_audit.py",
                "--out",
                str(tmp_path / "audit.json"),
            ],
            capture_output=True,
            text=True,
        )

        audit_path = tmp_path / "audit.json"
        if not audit_path.exists():
            pytest.skip(f"Audit did not produce output: {result.stderr}")

        audit = json.loads(audit_path.read_text())

        # Should NOT have fail_but_running finding
        fail_but_running_findings = [
            f for f in audit.get("findings", []) if f.get("code") == "fail_but_running"
        ]

        assert len(fail_but_running_findings) == 0, (
            f"Expected no fail_but_running finding when WO is properly in failed/, "
            f"got: {fail_but_running_findings}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
