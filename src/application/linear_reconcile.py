from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.domain.linear_models import LinearPolicy


_SEVERITY_ORDER = {"INFO": 1, "WARN": 2, "FATAL": 3}


def classify_drift(changed_fields: set[str], policy: LinearPolicy) -> str:
    normalized = set(changed_fields)
    if "state" in normalized:
        normalized.add("status_critical")

    highest = "INFO"
    for sev in ("INFO", "WARN", "FATAL"):
        mapped = set(policy.drift_severity.get(sev, ()))
        if normalized & mapped and _SEVERITY_ORDER[sev] > _SEVERITY_ORDER[highest]:
            highest = sev
    return highest


def diff_payload(projected: dict[str, Any], current: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = sorted(set(projected.keys()) | set(current.keys()))
    diffs: dict[str, dict[str, Any]] = {}
    for key in keys:
        if projected.get(key) != current.get(key):
            diffs[key] = {"projected": projected.get(key), "current": current.get(key)}
    return diffs


def write_reconcile_reports(
    root: Path,
    findings: list[dict[str, Any]],
    policy_version: str,
) -> tuple[Path, Path]:
    sync_dir = root / "_ctx" / "linear_sync"
    sync_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(findings, key=lambda x: x.get("wo_id", ""))
    json_path = sync_dir / "reconcile_report.json"
    md_path = sync_dir / "reconcile_report.md"

    payload = {
        "policy_version": policy_version,
        "findings": ordered,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = ["# Linear Reconcile Report", "", f"Policy version: `{policy_version}`", ""]
    if not ordered:
        lines.append("No drift detected.")
    else:
        for item in ordered:
            wo_id = item.get("wo_id", "unknown")
            sev = item.get("severity", "INFO")
            issue = item.get("linear_issue_id", "")
            lines.append(f"## {wo_id}")
            lines.append(f"- Severity: `{sev}`")
            if issue:
                lines.append(f"- Linear Issue: `{issue}`")
            changed = item.get("changed_fields", [])
            if changed:
                lines.append(f"- Changed Fields: {', '.join(changed)}")
            lines.append("")

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, md_path
