"""Integration test: Sidecar Trifecta plugin reads generated JSON index.

This test verifies that:
1. JSON export script generates valid index
2. Index is at correct location for Sidecar to read
3. Sidecar plugin can load and validate the JSON

Run with: uv run pytest tests/integration/test_sidecar_integration.py -v
"""
import json
import os
import subprocess
import shutil
from pathlib import Path

import pytest


class TestSidecarIntegration:
    """Test Sidecar ↔ Trifecta integration."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root path."""
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())

    @pytest.fixture
    def index_path(self, repo_root: Path) -> Path:
        """Path to generated index."""
        index_path = repo_root / "_ctx" / "index" / "wo_worktrees.json"
        subprocess.run(
            ["uv", "run", "python", "scripts/export_wo_index.py"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True,
        )
        return index_path

    def test_index_exists(self, index_path: Path):
        """G1: JSON index file exists."""
        assert index_path.exists(), f"Index not found at {index_path}"

    def test_index_is_valid_json(self, index_path: Path):
        """G2: Index is valid JSON."""
        with open(index_path) as f:
            data = json.load(f)
        assert isinstance(data, dict), "Index root should be object"

    def test_index_has_required_fields(self, index_path: Path):
        """G3: Index has all required fields."""
        with open(index_path) as f:
            data = json.load(f)

        required_fields = [
            "version",
            "schema",
            "generated_at",
            "repo_root",
            "git_head_sha_repo_root",
            "work_orders",
            "errors",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_schema_version_matches(self, index_path: Path):
        """G4: Schema version is correct."""
        with open(index_path) as f:
            data = json.load(f)

        assert data["version"] == 1, f"Unexpected version: {data['version']}"
        assert (
            data["schema"] == "trifecta.sidecar.wo_index.v1"
        ), f"Unexpected schema: {data['schema']}"

    def test_work_orders_is_list(self, index_path: Path):
        """G5: work_orders is a list."""
        with open(index_path) as f:
            data = json.load(f)

        assert isinstance(data["work_orders"], list), "work_orders should be array"

    def test_work_orders_have_required_fields(self, index_path: Path):
        """G6: Each WO has required fields."""
        with open(index_path) as f:
            data = json.load(f)

        if len(data["work_orders"]) == 0:
            pytest.skip("No work orders in index")

        wo_fields = [
            "id",
            "title",
            "status",
            "worktree_path",
            "worktree_exists",
            "branch",
            "wo_yaml_path",
        ]
        for i, wo in enumerate(data["work_orders"][:5]):  # Check first 5
            for field in wo_fields:
                assert field in wo, f"WO {i} missing field: {field}"

    def test_worktree_paths_are_relative(self, index_path: Path):
        """G7: worktree_path is relative (uses ../ for external)."""
        with open(index_path) as f:
            data = json.load(f)

        for wo in data["work_orders"]:
            # Path can be relative (../.worktrees) or within repo
            path = wo["worktree_path"]
            # Just verify it's a string and not absolute
            assert isinstance(path, str), f"worktree_path should be string"
            assert not path.startswith("/"), f"worktree_path should be relative, got: {path}"

    def test_repo_root_is_absolute(self, index_path: Path):
        """G8: repo_root is absolute path."""
        with open(index_path) as f:
            data = json.load(f)

        repo_root = data["repo_root"]
        assert repo_root.startswith("/"), f"repo_root should be absolute, got: {repo_root}"

    def test_sidecar_can_read_index(self, repo_root: Path, index_path: Path):
        """G9: Sidecar plugin path resolution works."""
        # Simulate Sidecar's IndexFilePath() logic
        relative_index = index_path.relative_to(repo_root)
        expected = Path("_ctx") / "index" / "wo_worktrees.json"
        assert relative_index == expected, f"Unexpected relative path: {relative_index}"

    def test_hooks_exist_in_scripts(self, repo_root: Path):
        """G10: Hook scripts exist that regenerate index."""
        take_script = repo_root / "scripts" / "ctx_wo_take.py"
        finish_script = repo_root / "scripts" / "ctx_wo_finish.py"
        export_script = repo_root / "scripts" / "export_wo_index.py"

        assert take_script.exists(), f"Take script not found: {take_script}"
        assert finish_script.exists(), f"Finish script not found: {finish_script}"
        assert export_script.exists(), f"Export script not found: {export_script}"

    def test_hooks_call_export(self, repo_root: Path):
        """G11: Hooks contain export script call."""
        take_script = repo_root / "scripts" / "ctx_wo_take.py"
        finish_script = repo_root / "scripts" / "ctx_wo_finish.py"

        take_content = take_script.read_text()
        finish_content = finish_script.read_text()

        # Both should call export_wo_index.py
        assert "export_wo_index.py" in take_content, "take script missing hook"
        assert "export_wo_index.py" in finish_content, "finish script missing hook"


def test_export_script_generates_valid_index():
    """G12: Running export script generates valid index."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/export_wo_index.py"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    assert result.returncode == 0, f"Export failed: {result.stderr}"

    # Verify output mentions index written
    assert "Index written to" in result.stdout
    assert "Work orders:" in result.stdout


def test_take_finish_updates_index_in_isolated_repo(tmp_path: Path):
    """take/finish should regenerate index with running->done transition."""
    script_repo = Path(__file__).parent.parent.parent
    root = tmp_path / "repo"
    root.mkdir()

    # Minimal repo structure required by ctx_wo_take/ctx_wo_finish
    (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)
    (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
    (root / "_ctx" / "jobs" / "done").mkdir(parents=True)
    (root / "_ctx" / "jobs" / "failed").mkdir(parents=True)
    (root / "_ctx" / "backlog").mkdir(parents=True)
    (root / "_ctx" / "dod").mkdir(parents=True)
    (root / "docs" / "backlog" / "schema").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)

    # Hook target scripts must exist under target repo root
    shutil.copy(script_repo / "scripts" / "export_wo_index.py", root / "scripts" / "export_wo_index.py")
    shutil.copy(script_repo / "scripts" / "paths.py", root / "scripts" / "paths.py")

    (root / "docs" / "backlog" / "schema" / "work_order.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["version", "id", "epic_id", "title", "priority", "status", "dod_id"],
                "properties": {
                    "version": {"type": "integer"},
                    "id": {"type": "string"},
                    "epic_id": {"type": "string"},
                    "title": {"type": "string"},
                    "priority": {"type": "string"},
                    "status": {"type": "string"},
                    "dod_id": {"type": "string"},
                    "scope": {"type": "object"},
                    "verify": {"type": "object"},
                },
                "additionalProperties": True,
            }
        ),
        encoding="utf-8",
    )

    (root / "_ctx" / "backlog" / "backlog.yaml").write_text(
        "version: 1\n"
        "generated_at: now\n"
        "epics:\n"
        "  - id: E-0001\n"
        "    title: Epic\n"
        "    priority: P1\n"
        "    wo_queue: [WO-0001]\n",
        encoding="utf-8",
    )
    (root / "_ctx" / "dod" / "DOD-DEFAULT.yaml").write_text(
        "dod:\n"
        "  - id: DOD-DEFAULT\n"
        "    checklist: []\n",
        encoding="utf-8",
    )
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        "version: 1\n"
        "id: WO-0001\n"
        "epic_id: E-0001\n"
        "title: Test WO\n"
        "priority: P1\n"
        "status: pending\n"
        "owner: null\n"
        "scope:\n"
        "  allow: ['scripts/**']\n"
        "  deny: ['.env*']\n"
        "verify:\n"
        "  commands: ['echo ok']\n"
        "dod_id: DOD-DEFAULT\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True, text=True)

    take = subprocess.run(
        ["python", str(script_repo / "scripts" / "ctx_wo_take.py"), "WO-0001", "--root", str(root)],
        cwd=script_repo,
        capture_output=True,
        text=True,
    )
    assert take.returncode == 0, take.stderr or take.stdout

    index_path = root / "_ctx" / "index" / "wo_worktrees.json"
    assert index_path.exists()
    take_index = json.loads(index_path.read_text(encoding="utf-8"))
    take_wo = next(wo for wo in take_index["work_orders"] if wo["id"] == "WO-0001")
    assert take_wo["status"] == "running"

    # finish requires clean git state
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "after take"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    finish = subprocess.run(
        [
            "python",
            str(script_repo / "scripts" / "ctx_wo_finish.py"),
            "WO-0001",
            "--root",
            str(root),
            "--skip-dod",
            "--result",
            "done",
        ],
        cwd=script_repo,
        capture_output=True,
        text=True,
    )
    assert finish.returncode == 0, finish.stderr or finish.stdout

    done_index = json.loads(index_path.read_text(encoding="utf-8"))
    done_wo = next(wo for wo in done_index["work_orders"] if wo["id"] == "WO-0001")
    assert done_wo["status"] == "done"
