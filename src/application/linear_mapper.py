from __future__ import annotations

from pathlib import Path
from typing import Any

from src.domain.linear_models import LinearPolicy


def _map_priority(value: Any) -> int:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return 3
    v = value.strip().lower()
    mapping = {
        "p0": 1,
        "p1": 2,
        "p2": 3,
        "p3": 4,
        "urgent": 1,
        "high": 2,
        "medium": 3,
        "normal": 3,
        "low": 4,
    }
    return mapping.get(v, 3)


def _render_read_only_section(title: str, lines: list[str]) -> str:
    body = "\n".join(lines) if lines else "(none)"
    return f"### {title} (read-only from Trifecta)\n{body}\n"


def _render_dod(wo: dict[str, Any]) -> list[str]:
    if isinstance(wo.get("dod"), list):
        items: list[str] = []
        for raw in wo["dod"]:
            if isinstance(raw, dict) and isinstance(raw.get("criterion"), str):
                items.append(f"- {raw['criterion']}")
            elif isinstance(raw, str):
                items.append(f"- {raw}")
        return items
    dod_id = wo.get("dod_id")
    if isinstance(dod_id, str) and dod_id:
        return [f"- dod_id: {dod_id}"]
    return []


def _render_verify_commands(wo: dict[str, Any]) -> list[str]:
    verify = wo.get("verify")
    if not isinstance(verify, dict):
        return []
    commands = verify.get("commands")
    if not isinstance(commands, list):
        return []
    return [f"- `{cmd}`" for cmd in commands if isinstance(cmd, str)]


def build_linear_payload(
    wo: dict[str, Any],
    policy: LinearPolicy,
    linear_state_id: str,
    wo_yaml_path: Path,
) -> dict[str, Any]:
    wo_id = str(wo.get("id") or "")
    title = str(wo.get("title") or "")
    objective = str(wo.get("objective") or wo.get("description") or "").strip()

    description_parts = [
        _render_read_only_section("Objective", [objective] if objective else []),
        _render_read_only_section("Definition of Done", _render_dod(wo)),
        _render_read_only_section("Verification Commands", _render_verify_commands(wo)),
        _render_read_only_section("Source", [f"- WO YAML: `{wo_yaml_path}`", f"- WO ID: `{wo_id}`"]),
    ]

    labels = ["trifecta", f"status:{wo.get('status', 'pending')}"]
    epic_id = wo.get("epic_id")
    if isinstance(epic_id, str) and epic_id:
        labels.append(f"epic:{epic_id}")

    owner = wo.get("owner")
    assignee = owner if isinstance(owner, str) and owner else None

    payload = {
        "wo_id": wo_id,
        "title": f"[{wo_id}] {title}".strip(),
        "description": "\n\n".join(description_parts).strip(),
        "priority": _map_priority(wo.get("priority", "medium")),
        "labels": sorted(set(labels)),
        "state": linear_state_id,
        "team": policy.team_id or policy.team_key,
        "status": wo.get("status", "pending"),
        "epic_id": epic_id if isinstance(epic_id, str) else "",
    }
    if assignee:
        payload["assignee"] = assignee
    if policy.project:
        payload["project"] = policy.project

    # Keep only policy-allowed outbound fields + wo_id anchor for remote lookup
    allowed = set(policy.outbound_allow) | {"wo_id", "status", "epic_id", "team"}
    return {k: v for k, v in payload.items() if k in allowed}
