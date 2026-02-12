#!/usr/bin/env python3
"""Work Order formatter for canonical YAML key order."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


CANONICAL_JOB_STATES = ("pending", "running", "done", "failed")
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
    "dependencies",
)


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


def _ordered(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in KEY_ORDER:
        if key in data:
            result[key] = data[key]
    for key in data:
        if key not in result:
            result[key] = data[key]
    return result


def _format_content(data: dict[str, Any]) -> str:
    ordered_data = _ordered(data)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Format Work Order YAML files")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--check", action="store_true", help="Only check formatting")
    parser.add_argument("--write", action="store_true", help="Rewrite files in canonical format")
    args = parser.parse_args()

    if args.check == args.write:
        parser.error("choose exactly one mode: --check or --write")

    root = Path(args.root).resolve()
    needs_format = 0
    changed = 0

    for path in _iter_wo_files(root):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            # Leave parse errors for the linter; formatter skips broken YAML.
            continue

        if not isinstance(data, dict):
            continue

        new_content = _format_content(data)
        old_content = path.read_text(encoding="utf-8")
        if new_content == old_content:
            continue

        if args.check:
            needs_format += 1
            print(f"Needs format: {path}")
        else:
            path.write_text(new_content, encoding="utf-8")
            changed += 1
            print(f"Formatted: {path}")

    if args.check:
        return 1 if needs_format else 0
    return 0 if changed >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
