#!/usr/bin/env python3
"""Work Order preflight - validate existing WO before take."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ctx_wo_lint import (
    SEVERITY_ERROR,
    SEVERITY_WARN,
    Finding,
    run as lint_run,
    _load_yaml,
)


CANONICAL_JOB_STATES = ("pending", "running", "done", "failed")


def resolve_wo_path(root: Path, wo_ref: str) -> Path | None:
    """Resolve WO reference (ID or path) to actual file path."""
    # If it's already a path
    if "/" in wo_ref or wo_ref.endswith(".yaml"):
        path = Path(wo_ref)
        if path.is_absolute():
            return path if path.exists() else None
        candidate = root / path
        return candidate if candidate.exists() else None

    # If it's a WO ID, search in state directories
    wo_id = wo_ref if wo_ref.startswith("WO-") else f"WO-{wo_ref}"
    for state in CANONICAL_JOB_STATES:
        candidate = root / "_ctx" / "jobs" / state / f"{wo_id}.yaml"
        if candidate.exists():
            return candidate
    return None


def check_canonical_format(wo_path: Path) -> Finding | None:
    """Check if WO file matches canonical format."""
    import yaml

    try:
        content = wo_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return Finding(
                SEVERITY_ERROR,
                "FMT001",
                "YAML root must be an object",
                str(wo_path),
            )

        # Check key ordering (simplified check)
        expected_order = (
            "version", "id", "epic_id", "title", "priority", "status",
            "owner", "branch", "worktree", "scope", "verify", "dod_id",
            "execution", "dependencies", "trace", "claim_links", "objective",
            "started_at", "finished_at", "result", "commit_sha",
            "verified_at_sha", "evidence_logs",
        )
        actual_keys = [k for k in data.keys() if k in expected_order]
        sorted_keys = sorted(actual_keys, key=lambda k: expected_order.index(k) if k in expected_order else 999)

        if actual_keys != sorted_keys:
            return Finding(
                SEVERITY_WARN,
                "FMT002",
                "Keys not in canonical order. Run: make wo-fmt",
                str(wo_path),
            )
        return None
    except Exception as e:
        return Finding(SEVERITY_ERROR, "FMT000", f"Format check error: {e}", str(wo_path))


def run_preflight(root: Path, wo_ref: str) -> tuple[bool, list[Finding], Path | None]:
    """Run preflight validation on a WO."""
    findings: list[Finding] = []

    # Resolve path
    wo_path = resolve_wo_path(root, wo_ref)
    if wo_path is None:
        findings.append(Finding(
            SEVERITY_ERROR,
            "WO_NOT_FOUND",
            f"WO '{wo_ref}' not found in any state directory",
            str(root / "_ctx" / "jobs"),
        ))
        return False, findings, None

    # Extract WO ID for lint
    wo_id = wo_path.stem

    # Run linter (strict mode)
    lint_findings = lint_run(root, strict=True, wo_id=wo_id)
    findings.extend(lint_findings)

    # Check format
    fmt_finding = check_canonical_format(wo_path)
    if fmt_finding:
        findings.append(fmt_finding)

    has_errors = any(f.severity == SEVERITY_ERROR for f in findings)
    return not has_errors, findings, wo_path


def format_human(passed: bool, findings: list[Finding], wo_path: Path | None, wo_ref: str) -> str:
    """Format output for human consumption."""
    lines: list[str] = []

    if passed and wo_path:
        lines.append(f"✓ {wo_ref} passes all validation gates")
        lines.append("")
        lines.append("Checks:")
        lines.append("  ✓ Schema validation")
        lines.append("  ✓ Execution contract")
        lines.append("  ✓ Epic ID reference")
        lines.append("  ✓ DoD reference")
        lines.append("  ✓ Scope structure")
        lines.append("  ✓ Verify commands")
        lines.append("  ✓ Dependencies")
        lines.append("  ✓ Format")
        lines.append("")
        lines.append(f"Ready to take: uv run python scripts/ctx_wo_take.py {wo_ref}")
    else:
        lines.append(f"✗ {wo_ref} failed validation")
        lines.append("")
        lines.append("Findings:")
        for f in findings:
            icon = "✗" if f.severity == SEVERITY_ERROR else "⚠"
            location = f" {f.path}" if f.path else ""
            lines.append(f"  {icon} [{f.code}]{location}: {f.message}")
        lines.append("")
        errors = sum(1 for f in findings if f.severity == SEVERITY_ERROR)
        warnings = sum(1 for f in findings if f.severity == SEVERITY_WARN)
        lines.append(f"Summary: {errors} error(s), {warnings} warning(s)")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Work Order before take (dry-run)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a pending WO
  uv run python scripts/ctx_wo_preflight.py WO-0047

  # Validate by path
  uv run python scripts/ctx_wo_preflight.py _ctx/jobs/pending/WO-0047.yaml

  # JSON output for CI
  uv run python scripts/ctx_wo_preflight.py WO-0047 --json
""",
    )
    parser.add_argument(
        "wo_ref",
        help="WO ID (WO-XXXX) or path to YAML file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    passed, findings, wo_path = run_preflight(root, args.wo_ref)

    if args.json:
        output: dict[str, Any] = {
            "passed": passed,
            "wo_ref": args.wo_ref,
            "wo_path": str(wo_path) if wo_path else None,
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_human(passed, findings, wo_path, args.wo_ref))

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
