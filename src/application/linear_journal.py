import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sync_dir(root: Path) -> Path:
    path = root / "_ctx" / "linear_sync"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _journal_path(root: Path) -> Path:
    return _sync_dir(root) / "index.jsonl"


def _state_path(root: Path) -> Path:
    return _sync_dir(root) / "state.json"


def append_journal_event(root: Path, event: dict[str, Any]) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    line = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    with _journal_path(root).open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _rebuild_state_from_journal(root: Path) -> dict[str, dict[str, str]]:
    state: dict[str, dict[str, str]] = {}
    path = _journal_path(root)
    if not path.exists():
        return state

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            row = json.loads(raw)
            wo_id = row.get("wo_id")
            if not isinstance(wo_id, str) or not wo_id:
                continue
            issue_id = row.get("linear_issue_id")
            fingerprint = row.get("last_fingerprint")
            policy_version = row.get("policy_version")
            updated_at = row.get("updated_at") or row.get("ts")
            if not all(isinstance(x, str) and x for x in [issue_id, fingerprint, policy_version, updated_at]):
                continue
            state[wo_id] = {
                "linear_issue_id": issue_id,
                "last_fingerprint": fingerprint,
                "policy_version": policy_version,
                "updated_at": updated_at,
            }

    return state


def write_state_snapshot(root: Path, state: dict[str, dict[str, str]]) -> None:
    ordered = {key: state[key] for key in sorted(state.keys())}
    _state_path(root).write_text(
        json.dumps(ordered, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def load_or_rebuild_state(root: Path) -> dict[str, dict[str, str]]:
    path = _state_path(root)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    rebuilt = _rebuild_state_from_journal(root)
    write_state_snapshot(root, rebuilt)
    return rebuilt
