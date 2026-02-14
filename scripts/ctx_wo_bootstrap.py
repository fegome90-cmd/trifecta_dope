#!/usr/bin/env python3
"""Work Order bootstrap - create valid WO YAML with fail-closed guarantees."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# Import linter for validation reuse
from ctx_wo_lint import (
    SEVERITY_ERROR,
    Finding,
    _load_dod_ids,
    _load_epic_ids,
    _load_yaml,
    _resolve_wo_path,
    run as lint_run,
)


# Canonical key order (must match ctx_wo_fmt.py)
KEY_ORDER = (
    "version",
    "id",
    "epic_id",
    "title",
    "priority",
    "status",
    "owner",
    "branch",
    "worktree",
    "scope",
    "verify",
    "dod_id",
    "execution",
    "dependencies",
    "trace",
    "claim_links",
    "objective",
    "started_at",
    "finished_at",
    "result",
    "commit_sha",
    "verified_at_sha",
    "evidence_logs",
)

# Internal template for new WOs
WO_TEMPLATE: dict[str, Any] = {
    "version": 1,
    "id": None,
    "epic_id": None,
    "title": None,
    "priority": "P2",
    "status": "pending",
    "owner": None,
    "branch": None,
    "worktree": None,
    "scope": {
        "allow": ["src/**", "tests/**", "docs/**"],
        "deny": [".env*", "**/production.*"],
    },
    "verify": {
        "commands": ["scripts/verify.sh"],
    },
    "dod_id": "DOD-DEFAULT",
    "execution": {
        "engine": "trifecta",
        "segment": ".",
        "required_flow": [
            "session.append:intent",
            "ctx.sync",
            "ctx.search",
            "ctx.get",
            "session.append:result",
        ],
    },
}

# Default required flow (5 mandatory steps)
DEFAULT_REQUIRED_FLOW = [
    "session.append:intent",
    "ctx.sync",
    "ctx.search",
    "ctx.get",
    "session.append:result",
]


class BootstrapError(Exception):
    """Bootstrap validation error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


def _ordered_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Order dict keys canonically (matches ctx_wo_fmt.py behavior)."""
    result: dict[str, Any] = {}
    for key in KEY_ORDER:
        if key in data:
            result[key] = data[key]
    for key in data:
        if key not in result:
            result[key] = data[key]
    return result


def _format_yaml(data: dict[str, Any]) -> str:
    """Format YAML with canonical ordering."""
    ordered_data = _ordered_dict(data)
    return (
        yaml.safe_dump(
            ordered_data,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=False,
            width=100,
        ).rstrip()
        + "\n"
    )


def validate_pre_write(
    root: Path,
    wo_id: str,
    epic_id: str,
    dod_id: str,
) -> None:
    """Validate that WO can be created (epic/dod exist, wo_id is unique)."""
    # Check WO ID doesn't exist in any state
    existing = _resolve_wo_path(root, wo_id)
    if existing is not None:
        state = _state_from_path(existing)
        raise BootstrapError(
            "WO_EXISTS",
            f"WO {wo_id} already exists in {state}/ directory: {existing}",
        )

    # Check epic_id exists
    epic_ids, _ = _load_epic_ids(root)
    if epic_id not in epic_ids:
        available = sorted(epic_ids) if epic_ids else ["(none)"]
        raise BootstrapError(
            "EPIC_NOT_FOUND",
            f"Epic '{epic_id}' not found. Available: {', '.join(available[:5])}{'...' if len(available) > 5 else ''}",
        )

    # Check dod_id exists
    dod_ids, _ = _load_dod_ids(root)
    if dod_id not in dod_ids:
        available = sorted(dod_ids) if dod_ids else ["(none)"]
        raise BootstrapError(
            "DOD_NOT_FOUND",
            f"DoD '{dod_id}' not found. Available: {', '.join(available[:5])}{'...' if len(available) > 5 else ''}",
        )


def _state_from_path(path: Path) -> str:
    """Extract state from path (pending/running/done/failed)."""
    for part in path.parts:
        if part in ("pending", "running", "done", "failed"):
            return part
    return "unknown"


def generate_wo_yaml(
    wo_id: str,
    epic_id: str,
    title: str,
    priority: str,
    dod_id: str,
    scope_allow: list[str],
    scope_deny: list[str],
    verify_cmds: list[str],
    dependencies: list[str] | None,
) -> dict[str, Any]:
    """Generate WO dict from template with user values."""
    wo = WO_TEMPLATE.copy()
    wo["id"] = wo_id
    wo["epic_id"] = epic_id
    wo["title"] = title
    wo["priority"] = _normalize_priority(priority)
    wo["dod_id"] = dod_id
    wo["scope"] = {
        "allow": scope_allow if scope_allow else WO_TEMPLATE["scope"]["allow"],
        "deny": scope_deny if scope_deny is not None else WO_TEMPLATE["scope"]["deny"],
    }
    wo["verify"] = {
        "commands": verify_cmds if verify_cmds else WO_TEMPLATE["verify"]["commands"],
    }
    if dependencies:
        wo["dependencies"] = dependencies
    return wo


def _normalize_priority(priority: str) -> str:
    """Normalize priority to canonical P0/P1/P2/P3 format."""
    priority_map = {
        "critical": "P0",
        "high": "P1",
        "medium": "P2",
        "low": "P3",
    }
    lower = priority.lower()
    if lower in priority_map:
        return priority_map[lower]
    if priority.upper() in ("P0", "P1", "P2", "P3"):
        return priority.upper()
    raise ValueError(f"Invalid priority '{priority}'. Use P0-P3 or critical/high/medium/low")


def verify_canonical_format(wo_path: Path) -> tuple[bool, str]:
    """Verify file matches canonical format (in-process, no subprocess)."""
    try:
        content = wo_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False, "YAML root must be an object"
        expected = _format_yaml(data)
        if content == expected:
            return True, ""
        return False, f"Format mismatch. Expected canonical ordering.\n--- Expected ---\n{expected}\n--- Got ---\n{content}"
    except Exception as e:
        return False, f"Format verification failed: {e}"


def run_bootstrap(
    root: Path,
    wo_id: str,
    epic_id: str,
    title: str,
    priority: str,
    dod_id: str,
    scope_allow: list[str],
    scope_deny: list[str],
    verify_cmds: list[str],
    dependencies: list[str] | None,
    dry_run: bool,
    register_epic: bool,
) -> tuple[int, str]:
    """Run bootstrap logic. Returns (exit_code, output_message)."""
    output_lines: list[str] = []

    # 1. Pre-write validation
    try:
        validate_pre_write(root, wo_id, epic_id, dod_id)
    except BootstrapError as e:
        output_lines.append(f"❌ {e.message}")
        return 1, "\n".join(output_lines)

    # 2. Generate WO from template
    try:
        wo_data = generate_wo_yaml(
            wo_id=wo_id,
            epic_id=epic_id,
            title=title,
            priority=priority,
            dod_id=dod_id,
            scope_allow=scope_allow,
            scope_deny=scope_deny,
            verify_cmds=verify_cmds,
            dependencies=dependencies,
        )
    except ValueError as e:
        output_lines.append(f"❌ {e}")
        return 1, "\n".join(output_lines)

    yaml_content = _format_yaml(wo_data)
    pending_dir = root / "_ctx" / "jobs" / "pending"
    wo_path = pending_dir / f"{wo_id}.yaml"

    # 3. Write file (or temp for dry-run)
    if dry_run:
        pending_dir.mkdir(parents=True, exist_ok=True)

    try:
        wo_path.write_text(yaml_content, encoding="utf-8")
    except Exception as e:
        output_lines.append(f"❌ Failed to write file: {e}")
        return 1, "\n".join(output_lines)

    # 4. Run lint validation
    findings = lint_run(root, strict=True, wo_id=wo_id)
    has_errors = any(f.severity == SEVERITY_ERROR for f in findings)

    if has_errors:
        # Fail-closed: delete the file
        wo_path.unlink(missing_ok=True)
        output_lines.append("❌ Generated WO failed lint validation. This is a bug in bootstrap.")
        for f in findings:
            if f.severity == SEVERITY_ERROR:
                output_lines.append(f"   [{f.code}] {f.message}")
        return 1, "\n".join(output_lines)

    # 5. Verify canonical format (in-process)
    fmt_passed, fmt_output = verify_canonical_format(wo_path)
    if not fmt_passed:
        # Fail-closed: delete the file
        wo_path.unlink(missing_ok=True)
        output_lines.append("❌ Generated WO failed format check. This is a bug in bootstrap.")
        output_lines.append(fmt_output)
        return 1, "\n".join(output_lines)

    # 6. Handle --dry-run
    if dry_run:
        wo_path.unlink(missing_ok=True)
        output_lines.append(f"✓ Dry-run: Would create {wo_path}")
        output_lines.append("")
        output_lines.append("--- Generated YAML ---")
        output_lines.append(yaml_content)
        output_lines.append("")
        output_lines.append("Validation:")
        output_lines.append("  ✓ Schema: PASS")
        output_lines.append("  ✓ Lint: PASS")
        output_lines.append("  ✓ Format: PASS")
        return 0, "\n".join(output_lines)

    # 7. Register epic (optional)
    if register_epic:
        # Note: This is a placeholder - actual implementation would modify backlog.yaml
        output_lines.append(f"⚠ --register-epic not implemented yet. Add {wo_id} to {epic_id}.wo_queue manually.")

    # 8. Success output
    output_lines.append(f"✓ Created: {wo_path}")
    output_lines.append("")
    output_lines.append(f"WO ID:     {wo_id}")
    output_lines.append(f"Epic:      {epic_id}")
    output_lines.append(f"Priority:  {wo_data['priority']}")
    output_lines.append(f"Title:     {title}")
    output_lines.append("")
    output_lines.append("Validation:")
    output_lines.append("  ✓ Schema: PASS")
    output_lines.append("  ✓ Lint: PASS")
    output_lines.append("  ✓ Format: PASS")
    output_lines.append("")
    output_lines.append("Next steps:")
    output_lines.append(f"  1. Review: cat {wo_path}")
    output_lines.append(f"  2. Take: uv run python scripts/ctx_wo_take.py {wo_id}")

    return 0, "\n".join(output_lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create Work Order scaffold with all required fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimum required
  uv run python scripts/ctx_wo_bootstrap.py \\
    --id WO-0047 --epic E-0001 --title "Feature description" \\
    --priority P1 --scope-allow "src/**" --verify-cmd "pytest"

  # With dry-run
  uv run python scripts/ctx_wo_bootstrap.py \\
    --id WO-TEST --epic E-0001 --title "Test" --dry-run
""",
    )
    parser.add_argument("--id", required=True, help="WO identifier (WO-XXXX)")
    parser.add_argument("--epic", required=True, dest="epic_id", help="Parent epic ID (E-XXXX)")
    parser.add_argument("--title", required=True, help="Descriptive title")
    parser.add_argument(
        "--priority",
        default="P2",
        help="Priority (P0/P1/P2/P3 or critical/high/medium/low)",
    )
    parser.add_argument(
        "--dod",
        default="DOD-DEFAULT",
        dest="dod_id",
        help="Definition of Done ID",
    )
    parser.add_argument(
        "--scope-allow",
        nargs="+",
        default=["src/**", "tests/**", "docs/**"],
        help="Scope allow patterns",
    )
    parser.add_argument(
        "--scope-deny",
        nargs="+",
        default=[".env*", "**/production.*"],
        help="Scope deny patterns",
    )
    parser.add_argument(
        "--verify-cmd",
        nargs="+",
        dest="verify_cmds",
        default=["scripts/verify.sh"],
        help="Verification commands (repeatable)",
    )
    parser.add_argument(
        "--deps",
        nargs="+",
        default=None,
        help="Dependency WO IDs (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show YAML without writing",
    )
    parser.add_argument(
        "--register-epic",
        action="store_true",
        help="Add WO to epic's wo_queue in backlog.yaml",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    exit_code, message = run_bootstrap(
        root=root,
        wo_id=args.id,
        epic_id=args.epic_id,
        title=args.title,
        priority=args.priority,
        dod_id=args.dod_id,
        scope_allow=args.scope_allow,
        scope_deny=args.scope_deny,
        verify_cmds=args.verify_cmds,
        dependencies=args.deps,
        dry_run=args.dry_run,
        register_epic=args.register_epic,
    )
    print(message)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
