"""Integration tests for status, doctor, and repo CLI commands."""

import json
import tempfile

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def test_status_command_basic():
    """Test basic status command output."""
    result = runner.invoke(app, ["status", "--repo", "."])
    assert result.exit_code == 0
    assert "Status for" in result.stdout
    assert "_ctx/" in result.stdout


def test_status_command_json():
    """Test status command with --json flag."""
    result = runner.invoke(app, ["status", "--repo", ".", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "repo_id" in data
    assert "path" in data
    assert "has_ctx_dir" in data


def test_doctor_command_basic():
    """Test basic doctor command output."""
    result = runner.invoke(app, ["doctor", "--repo", "."])
    assert result.exit_code == 0
    assert "Health Score:" in result.stdout


def test_doctor_command_json():
    """Test doctor command with --json flag."""
    result = runner.invoke(app, ["doctor", "--repo", ".", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "health_score" in data
    assert "issues" in data
    assert "warnings" in data


def test_repo_list_empty():
    """Test repo list when no repos registered."""
    result = runner.invoke(app, ["repo", "list"])
    assert result.exit_code == 0


def test_repo_register():
    """Test registering a repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, ["repo", "register", tmpdir])
        assert result.exit_code == 0
        assert "Registered:" in result.stdout


def test_repo_show():
    """Test showing a registered repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner.invoke(app, ["repo", "register", tmpdir])
        result = runner.invoke(app, ["repo", "list", "--json"])
        data = json.loads(result.stdout)
        repo_id = data["repos"][0]["repo_id"]

        result = runner.invoke(app, ["repo", "show", repo_id])
        assert result.exit_code == 0
        assert repo_id in result.stdout


def test_repo_show_not_found():
    """Test showing a non-existent repository."""
    result = runner.invoke(app, ["repo", "show", "nonexistent_id"])
    assert result.exit_code == 1
    output = result.stdout + (result.stderr or "")
    assert "not found" in output.lower()
