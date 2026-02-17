from pathlib import Path

import pytest
import yaml

from src.domain.linear_policy import LinearPolicyError, load_linear_policy


def _write_policy(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _base_policy() -> dict:
    return {
        "mode": "viewer",
        "direction": "outbound",
        "policy_version": "v1",
        "team_key": "TRI",
        "team_id": "team-123",
        "outbound_allow": [
            "title",
            "description",
            "priority",
            "labels",
            "assignee",
            "state",
            "comments",
        ],
        "inbound_allow": [],
        "drift_severity": {
            "INFO": ["description", "labels"],
            "WARN": ["priority", "assignee"],
            "FATAL": ["status_critical", "dod", "verify", "execution", "evidence"],
        },
        "status_map": {
            "pending": None,
            "running": None,
            "partial": None,
            "done": None,
            "failed": None,
        },
    }


def test_missing_required_key_fails_closed(tmp_path: Path) -> None:
    policy = _base_policy()
    policy.pop("mode")
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    with pytest.raises(LinearPolicyError, match="missing required key: mode"):
        load_linear_policy(policy_path)


def test_mode_must_be_viewer(tmp_path: Path) -> None:
    policy = _base_policy()
    policy["mode"] = "planner"
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    with pytest.raises(LinearPolicyError, match="mode must be 'viewer'"):
        load_linear_policy(policy_path)


def test_direction_must_be_outbound(tmp_path: Path) -> None:
    policy = _base_policy()
    policy["direction"] = "bidirectional"
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    with pytest.raises(LinearPolicyError, match="direction must be 'outbound'"):
        load_linear_policy(policy_path)


def test_inbound_allow_must_be_empty(tmp_path: Path) -> None:
    policy = _base_policy()
    policy["inbound_allow"] = ["title"]
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    with pytest.raises(LinearPolicyError, match="inbound_allow must be empty"):
        load_linear_policy(policy_path)


def test_team_key_or_team_id_required(tmp_path: Path) -> None:
    policy = _base_policy()
    policy["team_key"] = ""
    policy["team_id"] = ""
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    with pytest.raises(LinearPolicyError, match="team_key or team_id is required"):
        load_linear_policy(policy_path)


def test_valid_policy_loads(tmp_path: Path) -> None:
    policy = _base_policy()
    policy_path = tmp_path / "_ctx" / "policy" / "linear_sync_policy.yaml"
    _write_policy(policy_path, policy)

    loaded = load_linear_policy(policy_path)
    assert loaded.mode == "viewer"
    assert loaded.direction == "outbound"
    assert loaded.inbound_allow == ()
