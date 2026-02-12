#!/usr/bin/env python3
"""Work Order linter (schema + semantic consistency checks)."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate


CANONICAL_JOB_STATES = ("pending", "running", "done", "failed")
SEVERITY_ERROR = "ERROR"
SEVERITY_WARN = "WARN"


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    file: str
    path: str = ""
    hint: str = ""


def _e(code: str, message: str, file: Path, path: str = "", hint: str = "") -> Finding:
    return Finding(SEVERITY_ERROR, code, message, str(file), path, hint)


def _w(code: str, message: str, file: Path, path: str = "", hint: str = "") -> Finding:
    return Finding(SEVERITY_WARN, code, message, str(file), path, hint)


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [_e("YAML000", f"YAML parse error: {exc}", path)]
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, [_e("YAML001", "Root YAML must be an object", path)]
    return data, []


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_wo_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for state in CANONICAL_JOB_STATES:
        job_dir = root / "_ctx" / "jobs" / state
        if not job_dir.exists():
            continue
        for path in sorted(job_dir.glob("WO-*.yaml")):
            if "legacy" in path.parts:
                continue
            if path.name.endswith("_job.yaml") or path.name.endswith("-legacy.yaml"):
                continue
            paths.append(path)
    return paths


def _load_epic_ids(root: Path) -> set[str]:
    backlog_path = root / "_ctx" / "backlog" / "backlog.yaml"
    data = yaml.safe_load(backlog_path.read_text(encoding="utf-8")) or {}
    epics = data.get("epics", [])
    return {e.get("id") for e in epics if isinstance(e, dict) and e.get("id")}


def _load_dod_ids(root: Path) -> set[str]:
    dod_dir = root / "_ctx" / "dod"
    ids: set[str] = set()
    if not dod_dir.exists():
        return ids
    for path in sorted(dod_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for entry in data.get("dod", []):
            if isinstance(entry, dict) and entry.get("id"):
                ids.add(entry["id"])
    return ids


def _state_from_path(path: Path) -> str | None:
    for part in path.parts:
        if part in CANONICAL_JOB_STATES:
            return part
    return None


def lint_wo(
    wo: dict[str, Any],
    file_path: Path,
    epic_ids: set[str],
    dod_ids: set[str],
    seen_ids: set[str],
    known_wo_ids: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    file_id = file_path.stem
    wo_id = wo.get("id")
    if wo_id != file_id:
        findings.append(_e("WO002", f"id must match filename stem ({file_id})", file_path, "$.id"))
    if wo_id in seen_ids:
        findings.append(_e("WO003", f"Duplicate WO id: {wo_id}", file_path, "$.id"))
    elif isinstance(wo_id, str):
        seen_ids.add(wo_id)

    folder_state = _state_from_path(file_path)
    status = wo.get("status")
    if folder_state and status and str(status).lower() != folder_state:
        findings.append(
            _e(
                "WO004",
                f"status '{status}' does not match state folder '{folder_state}'",
                file_path,
                "$.status",
            )
        )

    epic_id = wo.get("epic_id")
    if epic_id and epic_id not in epic_ids:
        findings.append(_e("WO005", f"Unknown epic_id '{epic_id}'", file_path, "$.epic_id"))

    dod_id = wo.get("dod_id")
    if dod_id and dod_id not in dod_ids:
        findings.append(_e("WO006", f"Unknown dod_id '{dod_id}'", file_path, "$.dod_id"))

    scope = wo.get("scope", {})
    if not isinstance(scope, dict):
        findings.append(_e("WO007", "scope must be an object", file_path, "$.scope"))
    else:
        if not scope.get("allow") or scope.get("deny") is None:
            findings.append(_e("WO008", "scope.allow and scope.deny are required", file_path, "$.scope"))

    verify = wo.get("verify", {})
    commands = verify.get("commands") if isinstance(verify, dict) else None
    status_norm = str(status or "").lower()
    if status_norm in {"pending", "running"}:
        if not commands or not isinstance(commands, list) or not all(
            isinstance(x, str) and x.strip() for x in commands
        ):
            findings.append(
                _e(
                    "WO009",
                    "verify.commands must be a non-empty list of strings for pending/running WOs",
                    file_path,
                    "$.verify.commands",
                )
            )

    dependencies = wo.get("dependencies")
    if dependencies is not None:
        if not isinstance(dependencies, list):
            findings.append(_e("WO010", "dependencies must be a list", file_path, "$.dependencies"))
        else:
            for idx, dep in enumerate(dependencies):
                dep_path = f"$.dependencies[{idx}]"
                if not isinstance(dep, str) or not dep.startswith("WO-"):
                    findings.append(
                        _e("WO011", "dependency must be a WO id string (WO-...)", file_path, dep_path)
                    )
                    continue
                if dep not in known_wo_ids:
                    findings.append(
                        _e(
                            "WO012",
                            f"dependency references missing WO '{dep}'",
                            file_path,
                            dep_path,
                        )
                    )

    title = str(wo.get("title") or "").strip()
    if len(title) < 6:
        findings.append(_w("WOW01", "title is very short", file_path, "$.title"))

    return findings


def run(root: Path, strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    schema_path = root / "docs" / "backlog" / "schema" / "work_order.schema.json"
    wo_schema = _load_json(schema_path)
    epic_ids = _load_epic_ids(root)
    dod_ids = _load_dod_ids(root)

    seen_ids: set[str] = set()
    wo_paths = _iter_wo_files(root)
    known_wo_ids = {path.stem for path in wo_paths}
    for wo_path in wo_paths:
        wo, load_findings = _load_yaml(wo_path)
        findings.extend(load_findings)
        if wo is None:
            continue

        try:
            validate(instance=wo, schema=wo_schema)
        except Exception as exc:
            findings.append(_e("WOSCHEMA", str(exc), wo_path))
            continue

        findings.extend(lint_wo(wo, wo_path, epic_ids, dod_ids, seen_ids, known_wo_ids))

    if strict:
        findings = [
            Finding(SEVERITY_ERROR, f.code, f.message, f.file, f.path, f.hint)
            if f.severity == SEVERITY_WARN
            else f
            for f in findings
        ]

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Work Orders (schema + semantics)")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    findings = run(Path(args.root).resolve(), strict=args.strict)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for finding in findings:
            location = f" {finding.path}" if finding.path else ""
            hint = f" | hint: {finding.hint}" if finding.hint else ""
            print(f"[{finding.severity}] {finding.code}{location} {finding.file}: {finding.message}{hint}")
        errors = sum(1 for f in findings if f.severity == SEVERITY_ERROR)
        warnings = sum(1 for f in findings if f.severity == SEVERITY_WARN)
        print(f"Summary: {errors} error(s), {warnings} warning(s)")

    has_errors = any(f.severity == SEVERITY_ERROR for f in findings)
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
