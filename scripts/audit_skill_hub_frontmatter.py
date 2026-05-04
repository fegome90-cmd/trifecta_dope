#!/usr/bin/env python3
"""Audit malformed external SKILL.md frontmatter from the live skill-hub manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.domain.skill_hub_frontmatter_audit import (
    FrontmatterAuditTarget,
    audit_frontmatter_targets,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(Path.home() / ".trifecta/segments/skills-hub/_ctx/skills_manifest.json"),
        help="Path to skills_manifest.json (default: live global skill-hub manifest)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text",
    )
    return parser.parse_args()


def load_targets(manifest_path: Path) -> list[FrontmatterAuditTarget]:
    payload = json.loads(manifest_path.read_text())
    skills = payload["skills"] if isinstance(payload, dict) else payload
    targets: list[FrontmatterAuditTarget] = []
    for skill in skills:
        source_path = Path(skill["source_path"]).expanduser()
        targets.append(
            FrontmatterAuditTarget(
                source=str(skill.get("source", "")),
                name=str(skill.get("name", "")),
                source_path=str(source_path),
                content=source_path.read_text(errors="replace"),
            )
        )
    return targets


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser()
    report = audit_frontmatter_targets(load_targets(manifest_path))
    if args.json:
        payload = {
            "manifest": str(manifest_path),
            "total_targets": report.total_targets,
            "broken_count": report.broken_count,
            "failures": [
                {
                    "source": failure.source,
                    "name": failure.name,
                    "source_path": failure.source_path,
                    "error_family": failure.error_family,
                    "error_type": failure.error_type,
                    "error_message": failure.error_message,
                }
                for failure in report.failures
            ],
            "counts_by_error_type": report.count_by_error_type(),
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"manifest: {manifest_path}")
        print(f"total_targets: {report.total_targets}")
        print(f"broken_count: {report.broken_count}")
        for error_type, count in sorted(report.count_by_error_type().items()):
            print(f"- {error_type}: {count}")
        for failure in report.failures:
            print(
                f"[{failure.source}] {failure.name} | {failure.error_type} | "
                f"{failure.source_path}"
            )
    return 1 if report.broken_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
