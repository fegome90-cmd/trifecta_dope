from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.application.linear_fingerprint import compute_projection_fingerprint
from src.application.linear_journal import append_journal_event, load_or_rebuild_state, write_state_snapshot
from src.application.linear_mapper import build_linear_payload
from src.application.linear_reconcile import classify_drift, diff_payload, write_reconcile_reports
from src.domain.linear_models import REQUIRED_TRIFECTA_STATUSES, LinearPolicy
from src.domain.linear_policy import load_linear_policy
from src.infrastructure.linear_mcp_client import (
    LinearMCPCapabilityError,
    LinearMCPClient,
    LinearMCPError,
)


RECONCILE_EXIT_OK = 0
RECONCILE_EXIT_WARN = 2
RECONCILE_EXIT_FATAL = 3
RECONCILE_EXIT_TECH = 1

SYNC_EXIT_OK = 0
SYNC_EXIT_FATAL = 3
SYNC_EXIT_TECH = 1

BOOTSTRAP_EXIT_OK = 0
BOOTSTRAP_EXIT_TECH = 1


@dataclass
class LinearActionResult:
    ok: bool
    fatal: bool = False
    warn: bool = False
    message: str = ""
    exit_code: int = 0


class LinearSyncUseCase:
    def __init__(self, root: Path, mcp_client: LinearMCPClient | None = None):
        self.root = root.resolve()
        self.policy_path = self.root / "_ctx" / "policy" / "linear_sync_policy.yaml"
        self.status_map_path = self.root / "_ctx" / "linear_sync" / "status_map.json"
        self.policy: LinearPolicy = load_linear_policy(self.policy_path)
        self.client = mcp_client or LinearMCPClient()

    def _load_status_map_cache(self) -> dict[str, Any] | None:
        if not self.status_map_path.exists():
            return None
        try:
            data = json.loads(self.status_map_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None

        if data.get("policy_version") != self.policy.policy_version:
            return None

        team_id = str(data.get("team_id") or "").strip()
        if self.policy.team_id and team_id != self.policy.team_id:
            return None

        status_map = data.get("status_map")
        if not isinstance(status_map, dict):
            return None
        if any(not isinstance(status_map.get(s), str) or not status_map.get(s) for s in REQUIRED_TRIFECTA_STATUSES):
            return None
        return data

    def _save_status_map_cache(
        self,
        team_id: str,
        status_map: dict[str, str],
        linear_state_id_to_name: dict[str, str],
    ) -> None:
        self.status_map_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "team_id": team_id,
            "policy_version": self.policy.policy_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status_map": status_map,
            "linear_state_id_to_name": linear_state_id_to_name,
        }
        self.status_map_path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def bootstrap(self) -> LinearActionResult:
        try:
            self.client.check_capabilities()
            cached = self._load_status_map_cache()
            if cached:
                return LinearActionResult(ok=True, exit_code=BOOTSTRAP_EXIT_OK, message="status_map cache valid")

            team_id = self.policy.team_id
            if not team_id:
                resolved = self.client.resolve_team(self.policy.team_key)
                team_id = str(resolved.get("team_id") or "").strip()
            if not team_id:
                raise LinearMCPError("Unable to resolve Linear team_id")

            states_resp = self.client.list_workflow_states(team_id)
            states = states_resp.get("states")
            if not isinstance(states, list):
                raise LinearMCPError("list_workflow_states returned invalid payload")

            by_name: dict[str, str] = {}
            id_to_name: dict[str, str] = {}
            for item in states:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                state_id = str(item.get("id") or "").strip()
                if name and state_id:
                    by_name[name.lower()] = state_id
                    id_to_name[state_id] = name

            name_candidates = {
                "pending": ["todo", "backlog", "pending"],
                "running": ["in progress", "started"],
                "partial": ["in progress", "started"],
                "done": ["done", "completed"],
                "failed": ["canceled", "cancelled", "failed"],
            }
            resolved_map: dict[str, str] = {}
            for key, names in name_candidates.items():
                state_id = next((by_name[n] for n in names if n in by_name), "")
                if not state_id:
                    raise LinearMCPError(f"Missing required workflow state for '{key}'")
                resolved_map[key] = state_id

            self._save_status_map_cache(team_id=team_id, status_map=resolved_map, linear_state_id_to_name=id_to_name)
            return LinearActionResult(ok=True, exit_code=BOOTSTRAP_EXIT_OK)
        except (LinearMCPError, LinearMCPCapabilityError) as exc:
            return LinearActionResult(ok=False, exit_code=BOOTSTRAP_EXIT_TECH, message=str(exc))

    def doctor(self) -> LinearActionResult:
        """Run fail-closed diagnostics for viewer mode setup."""
        try:
            self.client.check_capabilities()
            cached = self._load_status_map_cache()
            if not cached:
                return LinearActionResult(
                    ok=False,
                    exit_code=BOOTSTRAP_EXIT_TECH,
                    message="status_map cache missing or invalid; run linear bootstrap",
                )
            return LinearActionResult(ok=True, exit_code=BOOTSTRAP_EXIT_OK, message="doctor ok")
        except (LinearMCPError, LinearMCPCapabilityError) as exc:
            return LinearActionResult(ok=False, exit_code=BOOTSTRAP_EXIT_TECH, message=str(exc))

    def _load_work_orders(self) -> list[tuple[dict[str, Any], Path]]:
        out: list[tuple[dict[str, Any], Path]] = []
        for state in ("pending", "running", "done", "failed"):
            state_dir = self.root / "_ctx" / "jobs" / state
            if not state_dir.exists():
                continue
            for wo_file in sorted(state_dir.glob("WO-*.yaml")):
                loaded = yaml.safe_load(wo_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    out.append((loaded, wo_file))
        return out

    def _status_map(self) -> dict[str, str]:
        cached = self._load_status_map_cache()
        if not cached:
            raise LinearMCPError("status_map cache missing or invalid; run linear bootstrap")
        return cached["status_map"]

    @staticmethod
    def _normalize_issue_for_diff(
        current: dict[str, Any],
        projected: dict[str, Any],
        linear_state_id_to_name: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        name_to_state_id: dict[str, str] = {}
        if isinstance(linear_state_id_to_name, dict):
            for sid, sname in linear_state_id_to_name.items():
                if isinstance(sid, str) and isinstance(sname, str):
                    name_to_state_id[sname.strip().lower()] = sid

        for key in projected.keys():
            value = current.get(key)
            if key == "state":
                if isinstance(value, dict):
                    value = value.get("id") or value.get("stateId") or value.get("name")
                if not value:
                    value = current.get("status")
                if isinstance(value, str):
                    lowered = value.strip().lower()
                    value = name_to_state_id.get(lowered, value)
            elif key == "priority" and isinstance(value, dict):
                value = value.get("value")
            elif key == "labels":
                if isinstance(value, list):
                    labels: list[str] = []
                    for item in value:
                        if isinstance(item, str):
                            labels.append(item)
                        elif isinstance(item, dict) and isinstance(item.get("name"), str):
                            labels.append(item["name"])
                    value = sorted(set(labels))
            elif key == "team":
                if isinstance(value, dict):
                    value = value.get("id") or value.get("key") or value.get("name")
                if current.get("teamId"):
                    value = current.get("teamId")
                elif not value:
                    value = current.get("team")
            elif key == "project":
                if isinstance(value, dict):
                    value = value.get("id") or value.get("name")
            elif key == "assignee" and isinstance(value, dict):
                value = value.get("id") or value.get("email") or value.get("name")

            normalized[key] = value
        return normalized

    def push_wo(self, wo_id: str) -> LinearActionResult:
        try:
            status_map = self._status_map()
            cache = self._load_status_map_cache() or {}
            resolved_team_id = str(cache.get("team_id") or "").strip()
            state = load_or_rebuild_state(self.root)
            wo_pair = next(((wo, path) for wo, path in self._load_work_orders() if wo.get("id") == wo_id), None)
            if wo_pair is None:
                raise LinearMCPError(f"WO not found: {wo_id}")
            wo, wo_path = wo_pair
            trifecta_status = str(wo.get("status") or "pending")
            linear_state_id = status_map.get(trifecta_status)
            if not linear_state_id:
                raise LinearMCPError(f"No status map for WO status '{trifecta_status}'")

            payload = build_linear_payload(wo, self.policy, linear_state_id, wo_path)
            if resolved_team_id:
                payload["team"] = resolved_team_id
            fingerprint = compute_projection_fingerprint(payload, self.policy.policy_version)
            comparable_keys = set(self.policy.outbound_allow) | {"team"}
            comparable_payload = {k: v for k, v in payload.items() if k in comparable_keys}

            entry = state.get(wo_id)
            if isinstance(entry, dict):
                issue_id = str(entry.get("linear_issue_id") or "")
            else:
                issue_id = ""

            if not issue_id:
                issues = self.client.list_issues(resolved_team_id or self.policy.team_id or self.policy.team_key)
                for issue in issues.get("issues", []):
                    if not isinstance(issue, dict):
                        continue
                    by_anchor = issue.get("wo_id") == wo_id
                    title = str(issue.get("title") or "")
                    by_title = title.startswith(f"[{wo_id}]")
                    if by_anchor or by_title:
                        issue_id = str(issue.get("id") or "")
                        if issue_id:
                            break

            if not issue_id:
                created = self.client.create_issue(payload)
                issue = created.get("issue") if isinstance(created, dict) else None
                issue_id = str((issue or {}).get("id") or "")
                if not issue_id and isinstance(created, dict):
                    issue_id = str(created.get("id") or "")
                if not issue_id:
                    raise LinearMCPError("create_issue did not return issue id")
                action = "create"
            else:
                current_resp = self.client.get_issue(issue_id)
                current = current_resp.get("issue") or {}
                current_norm = self._normalize_issue_for_diff(
                    current,
                    comparable_payload,
                    (cache.get("linear_state_id_to_name") if isinstance(cache, dict) else None),
                )
                diffs = diff_payload(comparable_payload, current_norm)
                changed_fields = set(diffs.keys())
                if not changed_fields and isinstance(entry, dict):
                    if str(entry.get("last_fingerprint") or "") == fingerprint:
                        return LinearActionResult(ok=True, exit_code=SYNC_EXIT_OK, message="noop")
                if changed_fields:
                    severity = classify_drift(changed_fields, self.policy)
                    if severity == "FATAL":
                        append_journal_event(
                            self.root,
                            {
                                "op": "push",
                                "wo_id": wo_id,
                                "linear_issue_id": issue_id,
                                "last_fingerprint": str(entry.get("last_fingerprint") if isinstance(entry, dict) else ""),
                                "policy_version": self.policy.policy_version,
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                                "severity": "FATAL",
                                "changed_fields": sorted(changed_fields),
                            },
                        )
                        return LinearActionResult(ok=False, fatal=True, exit_code=SYNC_EXIT_FATAL, message="fatal drift")
                self.client.update_issue(issue_id, payload)
                action = "update"

            if "state" in payload:
                self.client.transition_issue_state(issue_id, linear_state_id)
            if "labels" in payload:
                labels = payload.get("labels")
                if isinstance(labels, list):
                    self.client.set_labels(issue_id, labels)

            append_journal_event(
                self.root,
                {
                    "op": action,
                    "wo_id": wo_id,
                    "linear_issue_id": issue_id,
                    "last_fingerprint": fingerprint,
                    "policy_version": self.policy.policy_version,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            state[wo_id] = {
                "linear_issue_id": issue_id,
                "last_fingerprint": fingerprint,
                "policy_version": self.policy.policy_version,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            write_state_snapshot(self.root, state)
            return LinearActionResult(ok=True, exit_code=SYNC_EXIT_OK, message=action)
        except LinearMCPError as exc:
            return LinearActionResult(ok=False, exit_code=SYNC_EXIT_TECH, message=str(exc))

    def sync(self) -> LinearActionResult:
        fatal_count = 0
        for wo, _ in self._load_work_orders():
            wo_id = str(wo.get("id") or "")
            if not wo_id:
                continue
            res = self.push_wo(wo_id)
            if res.exit_code == SYNC_EXIT_TECH:
                return res
            if res.fatal:
                fatal_count += 1

        if fatal_count > 0:
            return LinearActionResult(ok=False, fatal=True, exit_code=SYNC_EXIT_FATAL, message=f"fatal_count={fatal_count}")
        return LinearActionResult(ok=True, exit_code=SYNC_EXIT_OK)

    def reconcile(self, dry_run: bool = True) -> LinearActionResult:
        try:
            status_map = self._status_map()
            findings: list[dict[str, Any]] = []
            max_sev = "INFO"

            state = load_or_rebuild_state(self.root)
            for wo, wo_path in self._load_work_orders():
                wo_id = str(wo.get("id") or "")
                entry = state.get(wo_id)
                if not isinstance(entry, dict):
                    continue
                issue_id = str(entry.get("linear_issue_id") or "")
                if not issue_id:
                    continue
                linear_state_id = status_map.get(str(wo.get("status") or "pending"))
                if not linear_state_id:
                    continue

                payload = build_linear_payload(wo, self.policy, linear_state_id, wo_path)
                comparable_keys = set(self.policy.outbound_allow) | {"team"}
                comparable_payload = {k: v for k, v in payload.items() if k in comparable_keys}
                current_resp = self.client.get_issue(issue_id)
                current = current_resp.get("issue") or {}
                if not isinstance(current, dict):
                    continue
                current_norm = self._normalize_issue_for_diff(
                    current,
                    comparable_payload,
                    (self._load_status_map_cache() or {}).get("linear_state_id_to_name"),
                )
                diffs = diff_payload(comparable_payload, current_norm)
                if not diffs:
                    continue
                changed_fields = set(diffs.keys())
                sev = classify_drift(changed_fields, self.policy)
                if sev == "FATAL":
                    max_sev = "FATAL"
                elif sev == "WARN" and max_sev != "FATAL":
                    max_sev = "WARN"

                findings.append(
                    {
                        "wo_id": wo_id,
                        "linear_issue_id": issue_id,
                        "severity": sev,
                        "changed_fields": sorted(changed_fields),
                        "dry_run": dry_run,
                    }
                )

            write_reconcile_reports(self.root, findings, self.policy.policy_version)

            if max_sev == "FATAL":
                return LinearActionResult(ok=False, fatal=True, exit_code=RECONCILE_EXIT_FATAL)
            if max_sev == "WARN":
                return LinearActionResult(ok=True, warn=True, exit_code=RECONCILE_EXIT_WARN)
            return LinearActionResult(ok=True, exit_code=RECONCILE_EXIT_OK)
        except LinearMCPError as exc:
            return LinearActionResult(ok=False, exit_code=RECONCILE_EXIT_TECH, message=str(exc))
