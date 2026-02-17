from pathlib import Path

import yaml

from src.application.linear_journal import load_or_rebuild_state
from src.application.linear_sync_use_case import SYNC_EXIT_OK, LinearSyncUseCase


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


def _write_wo(root: Path, wo_id: str) -> None:
    wo = {
        "id": wo_id,
        "epic_id": "E-0001",
        "title": "Test WO",
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


def test_push_is_idempotent_and_no_duplicates(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    _write_wo(tmp_path, "WO-0001")

    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    uc = LinearSyncUseCase(tmp_path)
    assert uc.bootstrap().ok

    first = uc.push_wo("WO-0001")
    second = uc.push_wo("WO-0001")

    assert first.exit_code == SYNC_EXIT_OK
    assert second.exit_code == SYNC_EXIT_OK

    issues = uc.client.list_issues("team-123")["issues"]
    uc.client.close()

    assert len(issues) == 1
    state = load_or_rebuild_state(tmp_path)
    assert state["WO-0001"]["linear_issue_id"] == issues[0]["id"]
