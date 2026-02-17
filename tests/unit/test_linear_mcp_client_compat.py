from __future__ import annotations

import json

import pytest

from src.infrastructure.linear_mcp_client import LinearMCPError
from src.infrastructure.linear_mcp_client import LinearMCPClient


def _mk_client() -> LinearMCPClient:
    return LinearMCPClient(command="cat")


def test_capabilities_accept_codex_linear_tool_names(monkeypatch) -> None:
    client = _mk_client()
    monkeypatch.setattr(
        client,
        "tools_list",
        lambda: [
            {"name": "create_issue"},
            {"name": "update_issue"},
            {"name": "get_issue"},
            {"name": "list_issues"},
            {"name": "create_comment"},
            {"name": "list_teams"},
            {"name": "list_issue_statuses"},
        ],
    )
    client.check_capabilities()


def test_resolve_team_via_list_teams(monkeypatch) -> None:
    client = _mk_client()
    monkeypatch.setattr(
        client,
        "tools_list",
        lambda: [
            {"name": "create_issue"},
            {"name": "update_issue"},
            {"name": "get_issue"},
            {"name": "list_issues"},
            {"name": "create_comment"},
            {"name": "list_teams"},
            {"name": "list_issue_statuses"},
        ],
    )

    def _call_tool(name: str, arguments: dict, retries: int = 3) -> dict:
        assert name == "list_teams"
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "teams": [
                                {"id": "team-abc", "name": "Trifecta Team"},
                                {"id": "team-def", "name": "Other"},
                            ]
                        }
                    ),
                }
            ]
        }

    monkeypatch.setattr(client, "call_tool", _call_tool)
    out = client.resolve_team("Trifecta Team")
    assert out["team_id"] == "team-abc"


def test_list_workflow_states_via_list_issue_statuses(monkeypatch) -> None:
    client = _mk_client()
    monkeypatch.setattr(
        client,
        "tools_list",
        lambda: [
            {"name": "create_issue"},
            {"name": "update_issue"},
            {"name": "get_issue"},
            {"name": "list_issues"},
            {"name": "create_comment"},
            {"name": "list_teams"},
            {"name": "list_issue_statuses"},
        ],
    )

    def _call_tool(name: str, arguments: dict, retries: int = 3) -> dict:
        assert name == "list_issue_statuses"
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        [
                            {"id": "st-todo", "name": "Todo"},
                            {"id": "st-progress", "name": "In Progress"},
                            {"id": "st-done", "name": "Done"},
                            {"id": "st-cancel", "name": "Canceled"},
                        ]
                    ),
                }
            ]
        }

    monkeypatch.setattr(client, "call_tool", _call_tool)
    out = client.list_workflow_states("team-abc")
    assert out["states"][0]["id"] == "st-todo"
    assert out["states"][1]["name"] == "In Progress"


def test_set_labels_and_transition_fallback_to_update_issue(monkeypatch) -> None:
    client = _mk_client()
    monkeypatch.setattr(
        client,
        "tools_list",
        lambda: [
            {"name": "create_issue"},
            {"name": "update_issue"},
            {"name": "get_issue"},
            {"name": "list_issues"},
            {"name": "create_comment"},
            {"name": "list_teams"},
            {"name": "list_issue_statuses"},
        ],
    )
    called: list[tuple[str, dict]] = []

    def _call_tool(name: str, arguments: dict, retries: int = 3) -> dict:
        called.append((name, arguments))
        return {"ok": True}

    monkeypatch.setattr(client, "call_tool", _call_tool)
    client.check_capabilities()
    client.set_labels("LIN-1", ["trifecta"])
    client.transition_issue_state("LIN-1", "st-progress")

    assert called[0][0] == "update_issue"
    assert called[0][1]["id"] == "LIN-1"
    assert called[0][1]["labels"] == ["trifecta"]
    assert called[1][0] == "update_issue"
    assert called[1][1]["id"] == "LIN-1"
    assert called[1][1]["state"] == "st-progress"


def test_decode_content_payload_fail_closed_invalid_shapes() -> None:
    with pytest.raises(LinearMCPError, match="has no text item"):
        LinearMCPClient._decode_content_payload({"content": []})

    with pytest.raises(LinearMCPError, match="not valid JSON"):
        LinearMCPClient._decode_content_payload(
            {"content": [{"type": "text", "text": "not-json"}]}
        )

    with pytest.raises(LinearMCPError, match="empty or invalid"):
        LinearMCPClient._decode_content_payload(
            {"content": [{"type": "text", "text": "   "}]}
        )


def test_decode_content_payload_fail_closed_size_limit() -> None:
    huge = "a" * (262144 + 1)
    with pytest.raises(LinearMCPError, match="exceeds max size"):
        LinearMCPClient._decode_content_payload(
            {"content": [{"type": "text", "text": huge}]}
        )


def test_alias_resolution_is_deterministic_and_logs_mapping_in_debug(monkeypatch) -> None:
    client = _mk_client()
    client.debug = True
    captured: list[tuple[str, str]] = []

    def _log(direction: str, frame: str) -> None:
        captured.append((direction, frame))

    monkeypatch.setattr(client, "_log", _log)
    monkeypatch.setattr(
        client,
        "tools_list",
        lambda: [
            {"name": "create_issue"},
            {"name": "update_issue"},
            {"name": "get_issue"},
            {"name": "list_issues"},
            {"name": "add_comment"},
            {"name": "create_comment"},
            {"name": "set_labels"},
            {"name": "transition_issue_state"},
            {"name": "resolve_team"},
            {"name": "list_workflow_states"},
        ],
    )
    client.check_capabilities()

    assert client._tool_map["add_comment"] == "add_comment"
    assert client._tool_map["set_labels"] == "set_labels"
    assert client._tool_map["transition_issue_state"] == "transition_issue_state"
    assert any("capability_map=" in frame for _, frame in captured)
