#!/usr/bin/env python3
"""
WO Audit Script - Forensic auditor for Trifecta Work Order state.

Idempotent: safe to run multiple times, never mutates state.
Output: structured JSON with findings, counts, and severity.

Usage:
    uv run python scripts/wo_audit.py --out data/wo_forensics/wo_audit.json
    uv run python scripts/wo_audit.py --out results.json --fail-on split_brain,running_without_lock
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FINDING_CODES = {
    "split_brain": "WO exists in multiple state directories simultaneously.",
    "running_without_lock": "WO in running/ has no corresponding .lock file.",
    "lock_without_running": "Lock file exists but no running YAML (stale lock).",
    "ghost_worktree": "Worktree exists in .worktrees/ but has no WO YAML in any state.",
    "zombie_worktree": "Worktree exists but WO is in a final state (done/failed).",
    "running_without_worktree": "WO is running but has no active worktree directory.",
    "duplicate_yaml": "Multiple YAML files for the same WO ID in one state dir (e.g. WO-0008 and WO-0008_job).",
    "pending_in_done": "WO YAML exists in both pending/ and done/.",
    "fail_but_running": "WO has verdict.json with status=FAIL but YAML still in running/ (transactional failure).",
}


def get_active_worktrees(repo_root: Path) -> dict[str, str]:
    """Returns {wo_id: worktree_path} for non-main worktrees."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )
    worktrees = {}
    current_path: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current_path = line[len("worktree ") :].strip()
        m = re.search(r"\.worktrees/(WO-[A-Za-z0-9._-]+)$", current_path or "")
        if m and current_path:
            worktrees[m.group(1)] = current_path
    return worktrees


def get_wo_states(repo_root: Path) -> dict[str, list[str]]:
    """Returns {wo_id: [states]} from _ctx/jobs/."""
    states = ["pending", "running", "done", "failed"]
    wo_state: dict[str, list[str]] = {}
    for s in states:
        d = repo_root / "_ctx" / "jobs" / s
        if not d.exists():
            continue
        for f in d.iterdir():
            if not f.name.endswith(".yaml"):
                continue
            if not f.name.startswith("WO-"):
                continue
            wo_id = f.stem  # e.g. WO-0008 or WO-0008_job
            wo_state.setdefault(wo_id, []).append(s)
    return wo_state


def get_locks(repo_root: Path) -> set[str]:
    running_dir = repo_root / "_ctx" / "jobs" / "running"
    if not running_dir.exists():
        return set()
    return {f.stem for f in running_dir.iterdir() if f.suffix == ".lock"}


def get_running_yamls(repo_root: Path) -> set[str]:
    running_dir = repo_root / "_ctx" / "jobs" / "running"
    if not running_dir.exists():
        return set()
    return {
        f.stem for f in running_dir.iterdir() if f.suffix == ".yaml" and f.stem.startswith("WO-")
    }


def normalize_wo_id(name: str) -> str:
    """Strip _job or similar suffixes to get base WO-XXXX id."""
    return (
        re.split(r"[_.]", name)[0]
        if "_" in name or ("." in name and not name.startswith("WO-P"))
        else name
    )


def audit(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    worktrees = get_active_worktrees(repo_root)
    wo_state = get_wo_states(repo_root)
    locks = get_locks(repo_root)
    running_yamls = get_running_yamls(repo_root)

    # Scrutinize states
    findings.extend(_find_split_brain(wo_state))
    findings.extend(_find_duplicate_yamls(wo_state))

    # Scrutinize locks
    findings.extend(_find_lock_issues(locks, running_yamls))

    # Scrutinize worktrees
    findings.extend(_find_worktree_scouts(worktrees, wo_state, running_yamls))

    # Scrutinize verdicts
    findings.extend(_find_verdict_failures(repo_root, running_yamls))

    # --- Summary ---
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["code"]] = counts.get(f["code"], 0) + 1

    unique_wos_seen = len({normalize_wo_id(wo_id) for wo_id in wo_state})

    return {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "git_head": _git_head(repo_root),
        "summary": {
            "total_findings": len(findings),
            "by_code": counts,
            "by_severity": {
                "P0": sum(1 for f in findings if f["severity"] == "P0"),
                "P1": sum(1 for f in findings if f["severity"] == "P1"),
                "P2": sum(1 for f in findings if f["severity"] == "P2"),
            },
            "worktrees_active": len(worktrees),
            "wos_total_unique": unique_wos_seen,
            "running_yamls": sorted(running_yamls),
            "locks_active": sorted(locks),
        },
        "findings": findings,
    }


def _find_split_brain(wo_state: dict[str, list[str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for wo_id, states in sorted(wo_state.items()):
        unique_states = list(dict.fromkeys(states))
        if len(unique_states) > 1:
            findings.append(
                {
                    "code": "split_brain",
                    "severity": "P0",
                    "wo_id": wo_id,
                    "states": unique_states,
                    "message": f"{wo_id} found in states: {unique_states}",
                    "invariant_violated": "Each WO must exist in exactly one state directory.",
                }
            )
    return findings


def _find_lock_issues(locks: set[str], running_yamls: set[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    # Running without lock
    for wo_id in sorted(running_yamls):
        if wo_id not in locks:
            findings.append(
                {
                    "code": "running_without_lock",
                    "severity": "P0",
                    "wo_id": wo_id,
                    "message": f"{wo_id} is in running/ but has no .lock file.",
                    "invariant_violated": "Every running WO must hold a lock file.",
                }
            )
    # Lock without running
    for wo_id in sorted(locks):
        if wo_id not in running_yamls:
            findings.append(
                {
                    "code": "lock_without_running",
                    "severity": "P1",
                    "wo_id": wo_id,
                    "message": f"Lock file exists for {wo_id} but no running YAML.",
                    "invariant_violated": "Lock files must correspond to an active running WO.",
                }
            )
    return findings


def _find_worktree_scouts(
    worktrees: dict[str, str], wo_state: dict[str, list[str]], running_yamls: set[str]
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for wt_id, wt_path in sorted(worktrees.items()):
        base_id = normalize_wo_id(wt_id)
        matched = any(normalize_wo_id(k) == base_id for k in wo_state)

        # Ghost worktree
        if not matched:
            findings.append(
                {
                    "code": "ghost_worktree",
                    "severity": "P0",
                    "wo_id": wt_id,
                    "worktree_path": wt_path,
                    "message": f"Worktree at {wt_path} has no WO YAML in any state.",
                    "invariant_violated": "Every worktree must have a corresponding WO YAML.",
                }
            )

        # Zombie worktree
        states = wo_state.get(wt_id, [])
        final_states = [s for s in states if s in ("done", "failed")]
        active_states = [s for s in states if s in ("pending", "running")]
        if final_states and not active_states:
            findings.append(
                {
                    "code": "zombie_worktree",
                    "severity": "P1",
                    "wo_id": wt_id,
                    "worktree_path": wt_path,
                    "final_states": final_states,
                    "message": f"Worktree alive for {wt_id} which is in {final_states}.",
                    "invariant_violated": "Completing a WO must remove its worktree.",
                }
            )

    # Running without worktree
    for wo_id in sorted(running_yamls):
        if wo_id not in worktrees:
            findings.append(
                {
                    "code": "running_without_worktree",
                    "severity": "P1",
                    "wo_id": wo_id,
                    "message": f"{wo_id} is running but no worktree found in .worktrees/.",
                    "invariant_violated": "Running WOs must have an active worktree.",
                }
            )
    return findings


def _find_verdict_failures(repo_root: Path, running_yamls: set[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    logs_dir = repo_root / "_ctx" / "logs"
    if not logs_dir.exists():
        return findings

    for wo_dir in logs_dir.iterdir():
        if not wo_dir.is_dir() or not wo_dir.name.startswith("WO-"):
            continue
        verdict_path = wo_dir / "verdict.json"
        if not verdict_path.exists():
            continue
        try:
            verdict = json.loads(verdict_path.read_text())
            if verdict.get("status") == "FAIL":
                wo_id = wo_dir.name
                if wo_id in running_yamls:
                    findings.append(
                        {
                            "code": "fail_but_running",
                            "severity": "P0",
                            "wo_id": wo_id,
                            "failure_stage": verdict.get("failure_stage"),
                            "finished_at": verdict.get("finished_at"),
                            "message": f"{wo_id} has FAIL verdict but still in running/ state.",
                            "invariant_violated": "FAIL verdict must trigger transition to failed/ state.",
                        }
                    )
        except (json.JSONDecodeError, OSError):
            continue
    return findings


def _find_duplicate_yamls(wo_state: dict[str, list[str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen: dict[str, list[str]] = {}
    for wo_id in wo_state:
        base = normalize_wo_id(wo_id)
        seen.setdefault(base, []).append(wo_id)

    for base, variants in sorted(seen.items()):
        if len(variants) > 1:
            all_states = []
            for v in variants:
                all_states.extend(wo_state.get(v, []))
            if len(all_states) != len(set(all_states)):
                findings.append(
                    {
                        "code": "duplicate_yaml",
                        "severity": "P2",
                        "wo_id": base,
                        "variants": variants,
                        "message": f"Multiple YAML files for same WO: {variants}",
                        "invariant_violated": "One WO ID must have exactly one canonical YAML.",
                    }
                )
    return findings


def _git_head(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="WO Forensic Auditor (read-only, idempotent)")
    parser.add_argument("--root", default=".", help="Repo root (default: .)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument(
        "--fail-on",
        default="",
        help="Comma-separated list of finding codes that trigger exit 1 if found",
    )
    parser.add_argument(
        "--fast-p0",
        action="store_true",
        help="Fast mode: only report P0 findings, skip P1/P2. Runtime <10s. "
        "Equivalent to filtering output to severity=P0 only.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    report = audit(repo_root)

    # Fail-on logic: check BEFORE --fast-p0 filtering to avoid silently hiding P1/P2
    # This ensures --fail-on works correctly even when --fast-p0 is used
    if args.fail_on:
        fail_codes = {c.strip() for c in args.fail_on.split(",") if c.strip()}
        original_codes = {f["code"] for f in report["findings"]}
        triggered = fail_codes & original_codes
        if triggered:
            # Even if --fast-p0 hides the finding, we still fail
            print(f"\nFAIL: --fail-on triggered for: {sorted(triggered)}", file=sys.stderr)
            if args.fast_p0:
                print(f"NOTE: Some triggered codes were P1/P2 and hidden by --fast-p0", file=sys.stderr)
            return 1

    # Fast P0 mode: filter to only P0 findings (after fail-on check)
    if args.fast_p0:
        report["findings"] = [f for f in report["findings"] if f.get("severity") == "P0"]
        # Recalculate summary
        s = report["summary"]
        p0_only = report["findings"]
        s["total_findings"] = len(p0_only)
        s["by_severity"] = {"P0": len(p0_only), "P1": 0, "P2": 0}
        s["by_code"] = {}
        for f in p0_only:
            s["by_code"][f["code"]] = s["by_code"].get(f["code"], 0) + 1
        s["fast_p0_mode"] = True

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"Report written to: {out_path}")

    # Print summary to stdout
    s = report["summary"]
    print(
        f"Findings: {s['total_findings']} total  (P0={s['by_severity']['P0']}  P1={s['by_severity']['P1']}  P2={s['by_severity']['P2']})"
    )
    for code, count in sorted(s["by_code"].items()):
        print(f"  {code}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
