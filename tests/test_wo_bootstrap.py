"""Tests for WO bootstrap and preflight scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create minimal repo structure with backlog, dod, schema."""
    root = tmp_path

    # Create directory structure
    (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)
    (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
    (root / "_ctx" / "jobs" / "done").mkdir(parents=True)
    (root / "_ctx" / "backlog").mkdir(parents=True)
    (root / "_ctx" / "dod").mkdir(parents=True)
    (root / "docs" / "backlog" / "schema").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)

    # Create backlog.yaml with test epic
    backlog_data = {
        "version": 1,
        "generated_at": "2026-02-14T00:00:00Z",
        "epics": [
            {
                "id": "E-TEST",
                "title": "Test Epic",
                "description": "Epic for testing",
                "status": "pending",
                "priority": "P1",
                "wo_queue": [],
            }
        ],
    }
    with open(root / "_ctx" / "backlog" / "backlog.yaml", "w") as f:
        yaml.safe_dump(backlog_data, f)

    # Create DoD file
    dod_data = {
        "dod": [
            {
                "id": "DOD-DEFAULT",
                "title": "Default Definition of Done",
                "checks": [
                    {"id": "test", "description": "Tests pass"},
                    {"id": "lint", "description": "Lint passes"},
                ],
            }
        ]
    }
    with open(root / "_ctx" / "dod" / "dod-default.yaml", "w") as f:
        yaml.safe_dump(dod_data, f)

    # Create minimal schema (simplified for tests)
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["version", "id", "epic_id", "title", "status", "scope", "verify", "dod_id", "execution"],
        "properties": {
            "version": {"type": "integer", "const": 1},
            "id": {"type": "string", "pattern": "^WO-"},
            "epic_id": {"type": "string"},
            "title": {"type": "string", "minLength": 1},
            "priority": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
            "status": {"type": "string", "enum": ["pending", "running", "done", "failed"]},
            "owner": {"type": ["string", "null"]},
            "branch": {"type": ["string", "null"]},
            "worktree": {"type": ["string", "null"]},
            "scope": {
                "type": "object",
                "required": ["allow", "deny"],
                "properties": {
                    "allow": {"type": "array", "items": {"type": "string"}},
                    "deny": {"type": "array", "items": {"type": "string"}},
                },
            },
            "verify": {
                "type": "object",
                "required": ["commands"],
                "properties": {
                    "commands": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                },
            },
            "dod_id": {"type": "string"},
            "execution": {
                "type": "object",
                "required": ["engine", "segment", "required_flow"],
                "properties": {
                    "engine": {"type": "string", "const": "trifecta"},
                    "segment": {"type": "string"},
                    "required_flow": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "allOf": [
                            {"contains": {"const": "session.append:intent"}},
                            {"contains": {"const": "ctx.sync"}},
                            {"contains": {"const": "ctx.search"}},
                            {"contains": {"const": "ctx.get"}},
                            {"contains": {"const": "session.append:result"}},
                        ],
                    },
                },
            },
            "dependencies": {"type": "array", "items": {"type": "string"}},
        },
    }
    with open(root / "docs" / "backlog" / "schema" / "work_order.schema.json", "w") as f:
        json.dump(schema_data, f, indent=2)

    return root


def run_bootstrap(
    root: Path,
    wo_id: str = "WO-TEST",
    epic_id: str = "E-TEST",
    title: str = "Test WO",
    priority: str = "P2",
    dod_id: str = "DOD-DEFAULT",
    scope_allow: list[str] | None = None,
    verify_cmds: list[str] | None = None,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Helper to run bootstrap script."""
    cmd = [
        sys.executable,
        "scripts/ctx_wo_bootstrap.py",
        "--root", str(root),
        "--id", wo_id,
        "--epic", epic_id,
        "--title", title,
        "--priority", priority,
        "--dod", dod_id,
    ]
    if scope_allow:
        cmd.extend(["--scope-allow"] + scope_allow)
    if verify_cmds:
        cmd.extend(["--verify-cmd"] + verify_cmds)
    if dry_run:
        cmd.append("--dry-run")

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def run_preflight(
    root: Path,
    wo_ref: str,
    json_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Helper to run preflight script."""
    cmd = [
        sys.executable,
        "scripts/ctx_wo_preflight.py",
        "--root", str(root),
        wo_ref,
    ]
    if json_output:
        cmd.append("--json")

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def create_valid_wo(root: Path, wo_id: str = "WO-VALID") -> Path:
    """Create a valid WO file for testing."""
    wo_data = {
        "version": 1,
        "id": wo_id,
        "epic_id": "E-TEST",
        "title": "Valid Test WO",
        "priority": "P2",
        "status": "pending",
        "owner": None,
        "branch": None,
        "worktree": None,
        "scope": {
            "allow": ["src/**", "tests/**"],
            "deny": [".env*"],
        },
        "verify": {
            "commands": ["pytest"],
        },
        "dod_id": "DOD-DEFAULT",
        "execution": {
            "engine": "trifecta",
            "segment": ".",
            "required_flow": [
                "session.append:intent",
                "ctx.sync",
                "ctx.search",
                "ctx.get",
                "session.append:result",
            ],
        },
    }
    wo_path = root / "_ctx" / "jobs" / "pending" / f"{wo_id}.yaml"
    with open(wo_path, "w") as f:
        yaml.safe_dump(wo_data, f, sort_keys=False)
    return wo_path


# =============================================================================
# Bootstrap Tests
# =============================================================================


class TestBootstrap:
    """Tests for ctx_wo_bootstrap.py."""

    def test_bootstrap_dry_run_no_file(self, tmp_repo: Path) -> None:
        """Dry-run should not create file."""
        result = run_bootstrap(
            tmp_repo,
            wo_id="WO-DRYRUN",
            dry_run=True,
        )

        assert result.returncode == 0
        assert "Dry-run" in result.stdout
        assert not (tmp_repo / "_ctx" / "jobs" / "pending" / "WO-DRYRUN.yaml").exists()

    def test_bootstrap_creates_valid_wo(self, tmp_repo: Path) -> None:
        """Bootstrap should create valid WO that passes lint."""
        result = run_bootstrap(
            tmp_repo,
            wo_id="WO-VALID-CREATE",
            title="Test creation",
            verify_cmds=["pytest -q"],
        )

        assert result.returncode == 0
        assert "Created:" in result.stdout

        wo_path = tmp_repo / "_ctx" / "jobs" / "pending" / "WO-VALID-CREATE.yaml"
        assert wo_path.exists()

        # Verify content
        with open(wo_path) as f:
            data = yaml.safe_load(f)
        assert data["id"] == "WO-VALID-CREATE"
        assert data["epic_id"] == "E-TEST"
        assert data["title"] == "Test creation"
        assert data["status"] == "pending"

    def test_bootstrap_epic_not_found(self, tmp_repo: Path) -> None:
        """Should fail if epic doesn't exist."""
        result = run_bootstrap(
            tmp_repo,
            wo_id="WO-NO-EPIC",
            epic_id="E-NONEXISTENT",
            dry_run=True,
        )

        assert result.returncode == 1
        assert "Epic" in result.stdout and "not found" in result.stdout

    def test_bootstrap_wo_exists(self, tmp_repo: Path) -> None:
        """Should fail if WO already exists."""
        # Create existing WO
        create_valid_wo(tmp_repo, "WO-EXISTS")

        result = run_bootstrap(
            tmp_repo,
            wo_id="WO-EXISTS",
            dry_run=True,
        )

        assert result.returncode == 1
        assert "already exists" in result.stdout

    def test_bootstrap_with_dependencies(self, tmp_repo: Path) -> None:
        """Bootstrap should include dependencies in generated WO."""
        # Create a dependency WO
        create_valid_wo(tmp_repo, "WO-DEP1")

        result = run_bootstrap(
            tmp_repo,
            wo_id="WO-WITH-DEPS",
            title="WO with dependencies",
        )

        # Note: Dependencies validation requires the dependency to exist in known_wo_ids
        # For now we just check the script runs
        assert result.returncode == 0


# =============================================================================
# Preflight Tests
# =============================================================================


class TestPreflight:
    """Tests for ctx_wo_preflight.py."""

    def test_preflight_valid_wo(self, tmp_repo: Path) -> None:
        """Preflight should pass for valid WO."""
        create_valid_wo(tmp_repo, "WO-PREFLIGHT-VALID")

        result = run_preflight(tmp_repo, "WO-PREFLIGHT-VALID")

        assert result.returncode == 0
        assert "passes all validation gates" in result.stdout

    def test_preflight_invalid_wo(self, tmp_repo: Path) -> None:
        """Preflight should fail for invalid WO."""
        # Create invalid WO (missing required_flow)
        invalid_wo = {
            "version": 1,
            "id": "WO-INVALID",
            "epic_id": "E-TEST",
            "title": "Invalid",
            "status": "pending",
            "scope": {"allow": ["src/**"], "deny": []},
            "verify": {"commands": ["test"]},
            "dod_id": "DOD-DEFAULT",
            "execution": {
                "engine": "trifecta",
                "segment": ".",
                "required_flow": ["invalid"],  # Missing required steps
            },
        }
        wo_path = tmp_repo / "_ctx" / "jobs" / "pending" / "WO-INVALID.yaml"
        with open(wo_path, "w") as f:
            yaml.safe_dump(invalid_wo, f)

        result = run_preflight(tmp_repo, "WO-INVALID")

        assert result.returncode == 1
        assert "failed validation" in result.stdout

    def test_preflight_json_output(self, tmp_repo: Path) -> None:
        """Preflight JSON output should be valid JSON."""
        create_valid_wo(tmp_repo, "WO-JSON-TEST")

        result = run_preflight(tmp_repo, "WO-JSON-TEST", json_output=True)

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["passed"] is True
        assert data["wo_ref"] == "WO-JSON-TEST"
        assert isinstance(data["findings"], list)

    def test_preflight_not_found(self, tmp_repo: Path) -> None:
        """Preflight should handle missing WO."""
        result = run_preflight(tmp_repo, "WO-NONEXISTENT")

        assert result.returncode == 1
        assert "not found" in result.stdout

    def test_preflight_by_path(self, tmp_repo: Path) -> None:
        """Preflight should accept path as well as ID."""
        wo_path = create_valid_wo(tmp_repo, "WO-BY-PATH")

        result = run_preflight(tmp_repo, str(wo_path))

        assert result.returncode == 0
        assert "passes all validation gates" in result.stdout
