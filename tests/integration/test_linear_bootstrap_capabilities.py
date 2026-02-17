import os
from pathlib import Path

import yaml

from src.application.linear_sync_use_case import BOOTSTRAP_EXIT_TECH, LinearSyncUseCase


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


def test_bootstrap_fails_when_required_capability_missing(tmp_path: Path, monkeypatch) -> None:
    _write_policy(tmp_path)
    monkeypatch.setenv("LINEAR_MCP_CMD", "python -m tests.fixtures.linear_mcp_fake")
    monkeypatch.setenv("LINEAR_FAKE_MISSING_CAPABILITY", "update_issue")
    monkeypatch.setenv("LINEAR_FAKE_DB", str(tmp_path / "fake_db.json"))

    uc = LinearSyncUseCase(tmp_path)
    res = uc.bootstrap()
    uc.client.close()

    assert res.exit_code == BOOTSTRAP_EXIT_TECH
    assert "missing required operations" in res.message.lower()
