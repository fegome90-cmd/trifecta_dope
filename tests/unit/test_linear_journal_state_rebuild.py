from pathlib import Path

from src.application.linear_journal import (
    append_journal_event,
    load_or_rebuild_state,
    write_state_snapshot,
)


def test_append_only_journal_and_rebuild_state(tmp_path: Path) -> None:
    root = tmp_path

    append_journal_event(
        root,
        {
            "op": "push",
            "wo_id": "WO-0001",
            "linear_issue_id": "LIN-1",
            "last_fingerprint": "abc",
            "policy_version": "v1",
            "updated_at": "2026-02-17T00:00:00Z",
        },
    )
    append_journal_event(
        root,
        {
            "op": "push",
            "wo_id": "WO-0001",
            "linear_issue_id": "LIN-1",
            "last_fingerprint": "def",
            "policy_version": "v1",
            "updated_at": "2026-02-17T01:00:00Z",
        },
    )

    state = load_or_rebuild_state(root)
    assert state["WO-0001"]["last_fingerprint"] == "def"


def test_rebuild_state_when_snapshot_is_corrupt(tmp_path: Path) -> None:
    root = tmp_path

    append_journal_event(
        root,
        {
            "op": "push",
            "wo_id": "WO-0002",
            "linear_issue_id": "LIN-2",
            "last_fingerprint": "xyz",
            "policy_version": "v1",
            "updated_at": "2026-02-17T00:00:00Z",
        },
    )

    state_path = root / "_ctx" / "linear_sync" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{not-json", encoding="utf-8")

    state = load_or_rebuild_state(root)
    assert state["WO-0002"]["linear_issue_id"] == "LIN-2"


def test_write_state_snapshot_is_deterministic_order(tmp_path: Path) -> None:
    root = tmp_path
    state = {
        "WO-0002": {
            "linear_issue_id": "LIN-2",
            "last_fingerprint": "bbb",
            "policy_version": "v1",
            "updated_at": "2026-02-17T02:00:00Z",
        },
        "WO-0001": {
            "linear_issue_id": "LIN-1",
            "last_fingerprint": "aaa",
            "policy_version": "v1",
            "updated_at": "2026-02-17T01:00:00Z",
        },
    }

    write_state_snapshot(root, state)
    text = (root / "_ctx" / "linear_sync" / "state.json").read_text(encoding="utf-8")
    assert text.find("WO-0001") < text.find("WO-0002")
