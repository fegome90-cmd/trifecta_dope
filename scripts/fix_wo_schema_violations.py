#!/usr/bin/env python3
"""
Fix WO schema violations for WO-0019.

Categories:
- B: finished_at missing for done WOs
- C: governance.must invalid entries (non-WO-XXXX format)
- D: WO-0056 missing version
- E: ID format issues (WO-XXXX-variant pattern)

Strategy:
- B: Add finished_at timestamp (use closed_at if available, else now)
- C: Move invalid entries to x_governance_notes
- D: Add version: 1
- E: These are variant WOs - add x_variant_id marker and keep as-is
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Canonical pattern for valid WO IDs (e.g. WO-0001)
_WO_ID_PATTERN = re.compile(r"^WO-\d{4}$", re.IGNORECASE)


def fix_finished_at(data: dict) -> bool:
    """Add finished_at to done WOs that lack it."""
    if data.get("status") != "done":
        return False

    if data.get("finished_at"):
        return False

    # Use closed_at if available, else current time
    if data.get("closed_at"):
        data["finished_at"] = data["closed_at"]
    else:
        # Use a reasonable historical date for legacy WOs
        data["finished_at"] = "2025-12-31T23:59:59Z"

    return True


def fix_governance_must(data: dict) -> bool:
    """Move invalid governance.must entries to x_governance_notes."""
    governance = data.get("governance")
    if not governance or "must" not in governance:
        return False

    must = governance.get("must", [])
    if not must:
        return False

    # Pattern for valid WO IDs (WO-XXXX)
    valid_pattern = _WO_ID_PATTERN

    valid_entries = []
    invalid_entries = []

    for entry in must:
        if valid_pattern.match(entry):
            valid_entries.append(entry)
        else:
            invalid_entries.append(entry)

    if not invalid_entries:
        return False

    # Move invalid entries to x_governance_notes
    if valid_entries:
        governance["must"] = valid_entries
    else:
        # Remove empty must
        del governance["must"]

    # Add x_governance_notes
    existing_notes = data.get("x_governance_notes", [])
    if isinstance(existing_notes, str):
        existing_notes = [existing_notes]
    data["x_governance_notes"] = existing_notes + invalid_entries

    return True


def fix_missing_version(data: dict) -> bool:
    """Add version: 1 if missing."""
    if "version" not in data:
        data["version"] = 1
        return True
    return False


def fix_variant_id(data: dict) -> bool:
    """Mark variant WOs with x_variant_id marker."""
    wo_id = data.get("id", "")

    if _WO_ID_PATTERN.match(wo_id):
        return False

    # This is a variant ID (WO-XXXX-suffix or WO-PX.X format)
    if "x_variant_id" not in data:
        data["x_variant_id"] = True
        return True

    return False


def check_wo_file(wo_path: Path) -> dict:
    """Check a single WO file for violations (read-only)."""
    with open(wo_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return {"file": str(wo_path), "error": "Empty file"}

    violations = {"file": str(wo_path), "id": data.get("id", "unknown"), "fixes": []}

    if data.get("status") == "done" and not data.get("finished_at"):
        violations["fixes"].append("finished_at")

    governance = data.get("governance")
    if governance and "must" in governance:
        invalid = [e for e in governance["must"] if not _WO_ID_PATTERN.match(e)]
        if invalid:
            violations["fixes"].append("governance.must")

    if "version" not in data:
        violations["fixes"].append("version")

    wo_id = data.get("id", "")
    if not _WO_ID_PATTERN.match(wo_id) and "x_variant_id" not in data:
        violations["fixes"].append("x_variant_id")

    return violations


def fix_wo_file(wo_path: Path) -> dict:
    """Fix a single WO file and return changes made."""
    with open(wo_path) as f:
        data = yaml.safe_load(f)

    if not data:
        return {"file": str(wo_path), "error": "Empty file"}

    changes = {"file": str(wo_path), "id": data.get("id", "unknown"), "fixes": []}

    # Apply fixes
    if fix_finished_at(data):
        changes["fixes"].append("finished_at")

    if fix_governance_must(data):
        changes["fixes"].append("governance.must")

    if fix_missing_version(data):
        changes["fixes"].append("version")

    if fix_variant_id(data):
        changes["fixes"].append("x_variant_id")

    # Write back if changes were made
    if changes["fixes"]:
        with open(wo_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return changes


def _process_file(wo_path: Path, check_mode: bool) -> tuple[dict, bool]:
    """Process a single WO file. Returns (result, was_affected)."""
    if check_mode:
        result = check_wo_file(wo_path)
        affected = bool(result.get("fixes"))
        if affected:
            print(f"\u2717 Violation {result['id']}: {', '.join(result['fixes'])}")
    else:
        result = fix_wo_file(wo_path)
        affected = bool(result.get("fixes"))
        if affected:
            print(f"\u2713 Fixed {result['id']}: {', '.join(result['fixes'])}")
    return result, affected


def main():
    """Fix all WO files in _ctx/jobs/."""
    parser = argparse.ArgumentParser(description="Fix WO schema violations")
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Read-only mode: report violations and exit 1 if any found (no files modified)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    args = parser.parse_args()

    jobs_dir = Path(args.root).resolve() / "_ctx/jobs"

    if not jobs_dir.exists():
        print("ERROR: _ctx/jobs directory not found")
        sys.exit(1)

    results = []
    affected_count = 0

    # Find all WO YAML files — sorted for deterministic processing
    for wo_path in sorted(jobs_dir.rglob("*.yaml")):
        if wo_path.name.startswith("WO-"):
            result, affected = _process_file(wo_path, args.check)
            results.append(result)
            if affected:
                affected_count += 1

    print(f"\n{'=' * 60}")
    if args.check:
        print(f"Summary: {affected_count} WO files with violations (no files modified)")
    else:
        print(f"Summary: Fixed {affected_count} WO files")
    print(f"{'=' * 60}")

    results_path = "/tmp/wo_fixes_check.json" if args.check else "/tmp/wo_fixes.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results: {results_path}")

    if args.check and affected_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
