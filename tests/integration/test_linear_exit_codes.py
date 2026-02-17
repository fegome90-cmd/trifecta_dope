from pathlib import Path

import yaml
from typer.testing import CliRunner

from src.application.linear_sync_use_case import LinearSyncUseCase
from src.infrastructure.cli import app


runner = CliRunner()


def _write_policy(root: Path) -> None:
    policy = {
        "mode": "viewer",
        "direction": "outbound",
        "policy_version": "v1",
        "team_key": "TRI",
        "team_id": "",
        "outbound_allow": ["title", "description", "priority", "labels", "assignee", "state", "comments"],
        "inbound_allow": [],
        "drift_severity": {
            "INFO": ["description", "labels"],
            "WARN": ["priority", "assignee"],
            "FATAL": ["status_critical", "dod", "verify", "execution", "evidence"],
        },
        "status_map": {"pending": None, "running": None, "partial": None, "done": None, "failed": None},
    }
    path = root / "_ctx" / "policy" / "linear_sync_policy.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")


def test_bootstrap_exit_code_ok(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    result = runner.invoke(app, ["linear", "bootstrap", "--root", str(tmp_path)])
    assert result.exit_code == 0


def _write_wo(root: Path, wo_id: str, title: str = "Test WO") -> None:
    wo = {
        "id": wo_id,
        "epic_id": "E-0001",
        "title": title,
        "priority": "P1",
        "status": "pending",
        "owner": None,
        "dod_id": "DOD-DEFAULT",
        "execution": {
            "engine": "trifecta",
            "required_flow": [
                "session.append:intent",
                "ctx.sync",
                "ctx.search",
                "ctx.get",
                "session.append:result",
            ],
            "segment": ".",
        },
    }
    wo_path = root / "_ctx" / "jobs" / "pending" / f"{wo_id}.yaml"
    wo_path.parent.mkdir(parents=True, exist_ok=True)
    wo_path.write_text(yaml.safe_dump(wo, sort_keys=False), encoding="utf-8")


def test_sync_exit_code_fatal_present(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    _write_wo(tmp_path, "WO-0001", "First")
    _write_wo(tmp_path, "WO-0002", "Second")
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    # Seed issues
    assert runner.invoke(app, ["linear", "push", "WO-0001", "--root", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["linear", "push", "WO-0002", "--root", str(tmp_path)]).exit_code == 0

    # Force fatal drift in WO-0001
    uc = LinearSyncUseCase(tmp_path)
    assert uc.bootstrap().ok
    issue_1 = uc.client.list_issues("team-123")["issues"][0]
    uc.client.transition_issue_state(issue_1["id"], "st-done")
    uc.client.close()

    result = runner.invoke(app, ["linear", "sync", "--root", str(tmp_path)])
    assert result.exit_code == 3


def test_reconcile_exit_code_fatal(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    _write_wo(tmp_path, "WO-0001", "First")
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    assert runner.invoke(app, ["linear", "push", "WO-0001", "--root", str(tmp_path)]).exit_code == 0

    uc = LinearSyncUseCase(tmp_path)
    assert uc.bootstrap().ok
    issue_1 = uc.client.list_issues("team-123")["issues"][0]
    uc.client.transition_issue_state(issue_1["id"], "st-done")
    uc.client.close()

    result = runner.invoke(app, ["linear", "reconcile", "--root", str(tmp_path), "--dry-run"])
    assert result.exit_code == 3


def test_doctor_exit_code_ok(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    assert runner.invoke(app, ["linear", "bootstrap", "--root", str(tmp_path)]).exit_code == 0
    result = runner.invoke(app, ["linear", "doctor", "--root", str(tmp_path)])
    assert result.exit_code == 0


def test_doctor_exit_code_tech_when_status_map_missing(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    result = runner.invoke(app, ["linear", "doctor", "--root", str(tmp_path)])
    assert result.exit_code == 1


def test_doctor_exit_code_tech_when_capability_missing(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    assert runner.invoke(app, ["linear", "bootstrap", "--root", str(tmp_path)]).exit_code == 0
    monkeypatch.setenv("LINEAR_FAKE_MISSING_CAPABILITY", "set_labels")

    result = runner.invoke(app, ["linear", "doctor", "--root", str(tmp_path)])
    assert result.exit_code == 1
