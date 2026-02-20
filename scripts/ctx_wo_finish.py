#!/usr/bin/env python3
"""
Work Order finish script with artifact generation and transaction safety.

Enhanced version that:
1. Generates DoD artifacts (tests.log, lint.log, diff.patch, handoff.md, verdict.json)
2. Validates artifacts with content checking
3. Executes finish as transaction with rollback on failure
4. Provides CLI flags for generate-only, clean, and skip-dod modes
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.domain.result import Result, Ok, Err
from src.cli.error_cards import render_error_card

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

REQUIRED_ARTIFACTS = ["tests.log", "lint.log", "diff.patch", "handoff.md", "verdict.json"]


# =============================================================================
# Policy-based Path Filtering (WO-0046)
# =============================================================================


def _glob_to_regex(pattern: str) -> str:
    """Convert glob pattern to regex for path matching."""
    i = 0
    result = ""
    while i < len(pattern):
        if pattern[i] == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                if i + 2 < len(pattern) and pattern[i + 2] == "/":
                    result += "(.+/)?"
                    i += 3
                else:
                    result += ".*"
                    i += 2
            else:
                result += "[^/]*"
                i += 1
        elif pattern[i] == "?":
            result += "[^/]"
            i += 1
        elif pattern[i] == ".":
            result += r"\."
            i += 1
        else:
            result += pattern[i]
            i += 1
    return f"^{result}$"


def path_matches_patterns(path: str, patterns: list[str]) -> bool:
    """Check if path matches any of the glob patterns."""
    for pattern in patterns:
        regex = _glob_to_regex(pattern)
        if re.match(regex, path):
            return True
    return False


def filter_paths_by_policy(
    paths: list[str], policy: dict[str, list[str]]
) -> tuple[list[str], list[str], list[str]]:
    """Filter paths using policy.

    Returns:
        (ignored_paths, blocked_paths, unknown_paths)
    """
    ignore = policy.get("ignore", [])
    allowlist = policy.get("allowlist_contract", [])

    ignored = []
    blocked = []
    unknown = []

    for path in paths:
        if path_matches_patterns(path, ignore):
            ignored.append(path)
        elif path_matches_patterns(path, allowlist):
            blocked.append(path)
        else:
            unknown.append(path)

    return ignored, blocked, unknown


def validate_policy_security(policy_path: Path, data: dict[str, object]) -> list[str]:
    """Validate policy file for security issues.

    Returns a list of warnings. Empty list means no issues found.
    """
    warnings = []
    ignore_patterns = _ensure_list(data.get("ignore", []))

    # Check for patterns that could hide malicious changes
    # Each risky pattern should have a SECURITY comment explaining the risk
    risky_patterns = [
        ("agent_*.md", "agent files can contain misleading prompts"),
        ("prime_*.md", "prime files can contain misleading documentation"),
        ("session_*.md", "session logs can hide malicious activity"),
    ]

    for risky_pattern, risk_desc in risky_patterns:
        if any(risky_pattern in p for p in ignore_patterns):
            # Check if SECURITY comment exists in file
            content = policy_path.read_text()
            if "SECURITY" not in content and "SECURITY ASSUMPTION" not in content:
                warnings.append(
                    f"Pattern '{risky_pattern}' is ignored but lacks SECURITY documentation. "
                    f"Risk: {risk_desc}. Add a SECURITY comment explaining why this is safe."
                )

    return warnings


def load_finish_policy(root: Path) -> dict[str, list[str]]:
    """Load ctx_finish_ignore.yaml policy if exists.

    Warns explicitly if policy file exists but cannot be parsed.
    Returns empty default on missing file or parse error (fail-soft).
    """
    policy_path = root / "_ctx" / "policy" / "ctx_finish_ignore.yaml"
    if not policy_path.exists():
        return {"ignore": [], "allowlist_contract": []}

    data = load_yaml(policy_path)
    if data is None:
        # File exists but failed to parse - warn explicitly
        logger.warning(
            f"Policy file exists but could not be parsed: {policy_path}. "
            "Using empty policy (no paths ignored/blocked). "
            "Fix YAML syntax or remove file to suppress this warning."
        )
        return {"ignore": [], "allowlist_contract": []}

    # Validate expected structure
    if not isinstance(data, dict):
        logger.warning(
            f"Policy file parsed but is not a dict: {policy_path} (got {type(data).__name__}). "
            "Using empty policy."
        )
        return {"ignore": [], "allowlist_contract": []}

    # Security validation
    security_warnings = validate_policy_security(policy_path, data)
    for warning in security_warnings:
        logger.warning(f"Policy security warning ({policy_path}): {warning}")

    # Ensure keys exist with defaults
    return {
        "ignore": _ensure_list(data.get("ignore")),
        "allowlist_contract": _ensure_list(data.get("allowlist_contract")),
    }


def _ensure_list(value: object) -> list[str]:
    """Ensure value is a list of strings, returning empty list if not."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    # Single value -> single-item list
    return [str(value)]


# =============================================================================
# Existing Utilities
# =============================================================================


def load_yaml(path: Path) -> dict[str, object] | None:
    """Load YAML file, returning None for empty files."""
    try:
        if not path.exists():
            return None
        content = path.read_text()
        if not content.strip():
            return None
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else None
    except (yaml.YAMLError, OSError, PermissionError) as e:
        logger.error(f"Failed to load YAML from {path}: {e}")
        return None


def print_error_card(
    *,
    error_code: str,
    cause: str,
    next_steps: list[str],
    verify_cmd: str,
    error_class: str = "PRECONDITION",
) -> None:
    """Print a stable error card plus backward-compatible plain error line."""
    card = render_error_card(
        error_code=error_code,
        error_class=error_class,
        cause=cause,
        next_steps=next_steps,
        verify_cmd=verify_cmd,
    )
    print(card, file=sys.stderr)
    print(f"ERROR: {cause}", file=sys.stderr)


def _ctx_running_path(wo_id: str, root: Path) -> Path:
    return root / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"


def write_yaml(path: Path, data: object) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def load_dod_catalog(root: Path) -> dict[str, dict[str, object]]:
    dod_dir = root / "_ctx" / "dod"
    catalog: dict[str, dict[str, object]] = {}
    for path in sorted(dod_dir.glob("*.yaml")):
        dod_data = load_yaml(path)
        if dod_data is not None:
            dod_entries = dod_data.get("dod")
            if isinstance(dod_entries, list):
                for entry in dod_entries:
                    if isinstance(entry, dict):
                        entry_id = entry.get("id", "")
                        catalog[entry_id] = entry
    return catalog


def resolve_runtime_root(root_input: str) -> Result[Path, str]:
    """Resolve canonical WO runtime root.

    Uses git common dir when available so calls from a worktree still resolve
    to the shared runtime root where `_ctx/jobs/*` state lives.
    """
    candidate = Path(root_input).expanduser().resolve()
    if not candidate.exists():
        return Err(f"INVALID_SEGMENT_PATH: root does not exist: {candidate}")
    if not candidate.is_dir():
        return Err(f"INVALID_SEGMENT_PATH: root is not a directory: {candidate}")

    try:
        show_toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=candidate,
            text=True,
        ).strip()
        common_dir_raw = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=candidate,
            text=True,
        ).strip()

        toplevel = Path(show_toplevel).resolve()
        common_dir = Path(common_dir_raw)
        if not common_dir.is_absolute():
            common_dir = (toplevel / common_dir).resolve()
        runtime_root = common_dir.parent

        if (runtime_root / "_ctx" / "jobs").exists():
            return Ok(runtime_root)
    except (subprocess.CalledProcessError, OSError):
        pass

    return Ok(candidate)


def update_worktree_index(root: Path) -> None:
    """Regenerate `_ctx/index/wo_worktrees.json` via export_wo_index.py."""
    export_script = root / "scripts" / "export_wo_index.py"
    if not export_script.exists():
        print(f"WARNING: skipped index update (missing {export_script})")
        return
    try:
        subprocess.run(
            ["uv", "run", "python", str(export_script)],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"WARNING: failed to update index via export_wo_index.py: {e}")


def run_verification_gate(wo_id: str, root: Path) -> Result[None, str]:
    """Run canonical verification workflow before closing WO."""
    verify_script = root / "scripts" / "verify.sh"
    if not verify_script.exists():
        return Err(f"Verification script missing: {verify_script}")

    try:
        result = subprocess.run(
            ["bash", str(verify_script), wo_id, "--root", str(root)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as e:
        return Err(f"Failed to run verification script: {e}")

    # verify.sh semantics: 0=pass, 1=blocking failure, 2=warnings only
    if result.returncode not in (0, 2):
        details = (result.stdout or result.stderr or "").strip().splitlines()
        tail = "\n".join(details[-12:]) if details else "no output"
        return Err(f"verify.sh failed (exit={result.returncode})\n{tail}")

    return Ok(None)


def run_scope_verification_gate(wo_id: str, root: Path) -> Result[None, str]:
    """Run WO-specific verify.commands gate via ctx_verify_run.sh."""
    scope_script = root / "scripts" / "ctx_verify_run.sh"
    if not scope_script.exists():
        return Err(f"Scope verification script missing: {scope_script}")

    try:
        result = subprocess.run(
            ["bash", str(scope_script), wo_id, "--root", str(root)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as e:
        return Err(f"Failed to run scope verification script: {e}")

    if result.returncode != 0:
        details = (result.stdout or result.stderr or "").strip().splitlines()
        tail = "\n".join(details[-12:]) if details else "no output"
        return Err(f"ctx_verify_run.sh failed (exit={result.returncode})\n{tail}")
    return Ok(None)


def validate_session_evidence(wo_id: str, root: Path) -> Result[None, str]:
    """Require intent/result evidence entries in session log."""
    session_path = root / "_ctx" / "session_trifecta_dope.md"
    if not session_path.exists():
        return Err(f"Session evidence file missing: {session_path}")

    content = session_path.read_text(encoding="utf-8")
    missing = []
    if f"[{wo_id}] intent:" not in content:
        missing.append("intent")
    if f"[{wo_id}] result:" not in content:
        missing.append("result")

    if missing:
        return Err(
            "Missing session evidence markers for "
            f"{wo_id}: {', '.join(missing)}. "
            f"Expected markers: [{wo_id}] intent: and [{wo_id}] result:"
        )
    return Ok(None)


def validate_scope_verdict(wo_id: str, root: Path) -> Result[None, str]:
    """Require PASS verdict generated by scope verification."""
    verdict_path = root / "_ctx" / "logs" / wo_id / "verdict.json"
    if not verdict_path.exists():
        return Err(f"Missing scope verification verdict: {verdict_path}")

    try:
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return Err(f"Malformed scope verdict JSON: {e}")

    status = str(verdict.get("status", "")).strip().upper()
    if status != "PASS":
        return Err(f"Scope verification verdict is not PASS: {status or 'missing'}")
    return Ok(None)


def write_scope_verification_report(wo_id: str, root: Path) -> Result[Path, str]:
    """Persist a deterministic verification report for closure evidence."""
    handoff_dir = root / "_ctx" / "handoff" / wo_id
    handoff_dir.mkdir(parents=True, exist_ok=True)
    report_path = handoff_dir / "verification_report.log"
    verdict_path = root / "_ctx" / "logs" / wo_id / "verdict.json"
    try:
        report_path.write_text(
            "\n".join(
                [
                    "Trifecta WO Scope Verification Report",
                    f"WO: {wo_id}",
                    f"Generated: {datetime.now(timezone.utc).isoformat()}",
                    "Status: PASS",
                    f"Verdict: {verdict_path}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    except OSError as e:
        return Err(f"Failed to write scope verification report: {e}")
    return Ok(report_path)


def inspect_nonrunning_state(wo_id: str, root: Path) -> str | None:
    """Return diagnostic string when running WO is missing but state exists elsewhere."""
    for state in ("done", "failed"):
        state_path = root / "_ctx" / "jobs" / state / f"{wo_id}.yaml"
        if not state_path.exists():
            continue
        try:
            state_data = load_yaml(state_path)
            if state_data is None:
                state_data = {}
        except yaml.YAMLError as e:
            logger.warning(f"Corrupted YAML in {state_path}: {e}")
            state_data = {"_parse_error": str(e)}
        except Exception as e:
            logger.warning(f"Cannot read {state_path}: {e}")
            state_data = {}

        status = str(state_data.get("status", "")).strip().lower()
        if status == "running":
            return (
                f"Corrupted WO state detected: {state_path} has status=running. "
                "Use scripts/ctx_reconcile_state.py before retrying."
            )
        return f"WO already closed in {state}/: {state_path}"
    return None


# =============================================================================
# Artifact Generation
# =============================================================================


def generate_artifacts(
    wo_id: str,
    root: Path,
    clean: bool = False,
) -> Result[Path, str]:
    """
    Generate all required DoD artifacts with proper error handling.

    Uses atomic temp-dir pattern: generate in .tmp directory, rename only on success.
    This prevents partial artifacts from previous runs.

    Args:
        wo_id: Work order ID (e.g., "WO-0012")
        root: Repository root path
        clean: If True, remove existing artifacts before regenerating

    Returns:
        Ok(handoff_dir) on success, Err(message) on failure
    """
    handoff_dir = root / "_ctx" / "handoff" / wo_id
    temp_dir = handoff_dir.with_suffix(".tmp")

    # Clean old artifacts if requested
    if clean and handoff_dir.exists():
        shutil.rmtree(handoff_dir)

    # Clean temp dir if exists
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # Create temp directory atomically
    try:
        temp_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return Err(f"Temp directory exists and cannot be cleaned: {temp_dir}")
    except OSError as e:
        return Err(f"Failed to create temp directory: {e}")

    try:
        # Generate tests.log with error handling
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "-m", "not slow", "-v"],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minutes
                cwd=root,
            )
            (temp_dir / "tests.log").write_text(result.stdout)
        except subprocess.CalledProcessError as e:
            # Tests may fail, but we still capture output
            output = e.stdout if e.stdout else e.stderr
            (temp_dir / "tests.log").write_text(output or f"Tests failed with exit {e.returncode}")
        except subprocess.TimeoutExpired:
            return Err("Tests timed out after 300 seconds")
        except OSError as e:
            return Err(f"Failed to write tests.log: {e}")

        # Generate lint.log
        ruff_exit_code = 0  # Default to passing
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "src/"],
                capture_output=True,
                text=True,
                check=False,  # Don't fail on lint errors
                timeout=60,
                cwd=root,
            )
            ruff_exit_code = result.returncode
            (temp_dir / "lint.log").write_text(result.stdout or "No lint issues")
        except subprocess.TimeoutExpired:
            return Err("Lint timed out")
        except OSError as e:
            return Err(f"Failed to write lint.log: {e}")

        # Generate diff.patch with policy filtering
        try:
            BASE_BRANCH = "origin/main"

            # Fetch origin to ensure we have latest main
            try:
                subprocess.run(
                    ["git", "fetch", "origin"],
                    capture_output=True,
                    check=False,
                    timeout=30,
                    cwd=root,
                )
            except subprocess.TimeoutExpired:
                return Err("Git fetch timed out")
            except OSError as e:
                return Err(f"Git fetch failed: {e}")

            # First, get the list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--merge-base", BASE_BRANCH, "HEAD"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                cwd=root,
            )
            changed_files = [f for f in result.stdout.splitlines() if f.strip()]

            # Separate _ctx/ paths from other paths
            # Policy only applies to _ctx/ paths - other paths are always allowed
            ctx_paths = [f for f in changed_files if f.startswith("_ctx/")]
            other_paths = [f for f in changed_files if not f.startswith("_ctx/")]

            # Apply policy filtering ONLY to _ctx/ paths
            policy = load_finish_policy(root)
            ignored, blocked, unknown = filter_paths_by_policy(ctx_paths, policy)

            # If there are unknown _ctx paths, fail closed
            if unknown:
                unknown_list = "\n  - ".join(unknown)
                policy_path_str = str(root / "_ctx" / "policy" / "ctx_finish_ignore.yaml")
                return Err(
                    f"UNKNOWN_PATHS: WO has changes to unclassified _ctx paths:\n  - {unknown_list}\n"
                    f"These paths are not in ignore nor allowlist_contract.\n"
                    f"Classify them in: {policy_path_str}\n"
                    f"Ignore: {policy.get('ignore', [])}\n"
                    f"Allowlist: {policy.get('allowlist_contract', [])}"
                )

            # If there are blocked _ctx paths (contract/state-machine changes), fail
            if blocked:
                blocked_list = "\n  - ".join(blocked)
                return Err(
                    f"BLOCKED_PATHS: WO has changes to contract/state-machine paths:\n  - {blocked_list}\n"
                    f"These paths cannot be modified as part of this WO: {policy.get('allowlist_contract', [])}"
                )

            # Calculate allowed files: non-ctx paths (always allowed) + allowed ctx paths
            ignored_set = set(ignored)
            allowed_files = other_paths + [f for f in ctx_paths if f not in ignored_set]

            # Generate diff for allowed paths only
            if allowed_files:
                result = subprocess.run(
                    ["git", "diff", "--merge-base", BASE_BRANCH, "HEAD", "--"] + allowed_files,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                    cwd=root,
                )
                diff_content = result.stdout
            else:
                diff_content = "No changes from merge-base"

            (temp_dir / "diff.patch").write_text(diff_content or "No changes from main")
        except subprocess.TimeoutExpired:
            return Err("Git diff timed out")
        except OSError as e:
            return Err(f"Failed to write diff.patch: {e}")

        # Generate handoff.md from WO metadata
        wo_path = root / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
        if not wo_path.exists():
            return Err(f"WO file not found: {wo_path}")

        wo_data = yaml.safe_load(wo_path.read_text())

        handoff_md = f"""# Handoff: {wo_id}

## Summary
{wo_data.get("x_objective", "No objective provided")}

## Evidence
"""
        for task in wo_data.get("x_micro_tasks", []):
            if task.get("status") == "done":
                evidence = (
                    task.get("evidence", ["No evidence"])[0]
                    if isinstance(task.get("evidence"), list)
                    else task.get("evidence", "No evidence")
                )
                handoff_md += f"\n- {task['name']}: {evidence}\n"

        (temp_dir / "handoff.md").write_text(handoff_md)

        # Parse tests.log for failing tests
        failing_tests = []
        try:
            tests_output = (temp_dir / "tests.log").read_text()
            # Extract failed test names from pytest output
            failed_match = re.search(r"FAILED\s+(.+)", tests_output)
            if failed_match:
                failed_line = failed_match.group(1)
                # Parse failed test names (format: "path/to/test.py::test_name")
                for test_path in failed_line.split():
                    if "::" in test_path:
                        test_name = test_path.split("::")[-1]
                        failing_tests.append({"name": test_name, "reason": "Test failed"})
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to parse tests.log for failing tests: {e}")

        # Generate verdict.json with schema validation
        verdict = {
            "wo_id": wo_id,
            "status": "done",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tests_passed": len(failing_tests) == 0,
            "failing_tests": failing_tests,
            "lint_passed": ruff_exit_code == 0,  # Parse ruff exit code: 0 = no issues
            "artifact_verification": "complete",
            "notes": f"Validation for {wo_id}",
        }
        (temp_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))

        # Atomic rename only after ALL artifacts generated
        temp_dir.rename(handoff_dir)
        return Ok(handoff_dir)

    except subprocess.TimeoutExpired as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return Err(f"ARTIFACT_TIMEOUT: {e.cmd} timed out after {e.timeout}s")
    except OSError as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return Err(f"ARTIFACT_IO_ERROR: {type(e).__name__}: {e}")
    except Exception as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return Err(f"ARTIFACT_UNEXPECTED_ERROR: {type(e).__name__}: {e}")


# =============================================================================
# DoD Validation
# =============================================================================


def validate_minimum_evidence(wo_id: str, root: Path) -> Result[None, str]:
    """
    Fail-closed validation of required DoD artifacts.
    Checks existence AND content validity.

    Args:
        wo_id: Work order ID
        root: Repository root path

    Returns:
        Ok(None) if valid, Err(message) if validation fails
    """
    handoff_dir = root / "_ctx" / "handoff" / wo_id

    # Check directory exists and is valid
    if not handoff_dir.exists():
        return Err(f"EVIDENCE_MISSING: handoff directory missing: {handoff_dir}")
    if not handoff_dir.is_dir():
        return Err(f"Handoff path exists but is not a directory: {handoff_dir}")

    # Check for .tmp marker indicating interrupted generation
    tmp_marker = handoff_dir / ".generation_in_progress"
    if tmp_marker.exists():
        return Err(
            f"Artifact generation was interrupted for {wo_id}. "
            f"Re-run: python scripts/ctx_wo_finish.py {wo_id} --generate-only --clean"
        )

    # Check tests.log first when present so empty logs are caught deterministically.
    tests_log = handoff_dir / "tests.log"
    if tests_log.exists():
        if tests_log.stat().st_size == 0:
            return Err("EVIDENCE_INVALID: tests.log is empty - pytest may have failed silently")
        try:
            content = tests_log.read_text()
        except (OSError, PermissionError) as e:
            return Err(f"EVIDENCE_INVALID: cannot read tests.log: {e}")
        if content.count("ERROR") > 10:
            return Err(f"EVIDENCE_INVALID: tests.log contains {content.count('ERROR')} errors")

    # verdict.json is mandatory.
    verdict_file = handoff_dir / "verdict.json"
    if not verdict_file.exists():
        return Err("EVIDENCE_MISSING: missing DoD artifacts: ['verdict.json']")

    try:
        verdict = json.loads(verdict_file.read_text())
        if "wo_id" not in verdict or verdict["wo_id"] != wo_id:
            return Err("EVIDENCE_INVALID: verdict.json missing or invalid wo_id")
        if "status" not in verdict:
            return Err("EVIDENCE_INVALID: verdict.json missing status field")
    except json.JSONDecodeError as e:
        return Err(f"EVIDENCE_INVALID: verdict.json is malformed: {e}")

    return Ok(None)


def validate_dod(wo_id: str, root: Path) -> Result[None, str]:
    """Legacy compatibility wrapper kept for integration tests."""
    handoff_dir = root / "_ctx" / "handoff" / wo_id
    if not handoff_dir.exists():
        return Err(f"Handoff directory missing for {wo_id}")

    # Legacy contract expected this full artifact set.
    missing = [a for a in REQUIRED_ARTIFACTS if not (handoff_dir / a).exists()]
    if missing:
        return Err(f"Missing DoD artifacts: {missing}")

    result = validate_minimum_evidence(wo_id, root)
    if result.is_ok():
        return result

    err = result.unwrap_err()
    if "handoff directory missing" in err.lower():
        return Err(f"Handoff directory missing for {wo_id}")
    if "missing dod artifacts" in err.lower():
        return Err(f"Missing DoD artifacts: {err}")
    if "tests.log is empty" in err.lower():
        return Err("tests.log is empty")
    if "verdict.json is malformed" in err.lower():
        return Err("verdict.json malformed")

    return Err(err)


# =============================================================================
# Transaction Wrapper
# =============================================================================


def finish_wo_transaction(
    wo_id: str,
    root: Path,
    result: Literal["done", "failed"],
) -> Result[None, str]:
    """
    Execute WO finish as a transaction with automatic rollback on failure.
    Prevents split-brain state if process crashes mid-operation.

    Args:
        wo_id: Work order ID
        root: Repository root path
        result: "done" or "failed"

    Returns:
        Ok(None) on success, Err(message) on failure
    """
    running_path = root / "_ctx" / "jobs" / "running" / f"{wo_id}.yaml"
    done_path = root / "_ctx" / "jobs" / result / f"{wo_id}.yaml"
    lock_path = root / "_ctx" / "jobs" / "running" / f"{wo_id}.lock"

    # Validate prerequisites
    if not running_path.exists():
        return Err(f"WO not in running/: {running_path}")

    # Load WO data
    wo = yaml.safe_load(running_path.read_text())

    # Validate git state
    try:
        # Check for uncommitted changes
        git_status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=no",
                "--",
                ".",
                f":(exclude)_ctx/handoff/{wo_id}",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=root,
        )
        if git_status.stdout.strip():
            return Err("Repository has uncommitted changes. Commit or stash before finishing WO.")

        # Check not in detached HEAD
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            text=True,
        ).strip()
        if branch == "HEAD":
            return Err("Detached HEAD state. WOs must be finished from a branch.")

        # Capture commit SHA
        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as e:
        return Err(f"Git state validation failed: {e}")

    # Transaction operations
    ops_completed = []

    try:
        # Operation 1: Create result directory
        done_path.parent.mkdir(parents=True, exist_ok=True)
        ops_completed.append("create_result_dir")

        # Operation 2: Update WO metadata
        wo["status"] = result
        wo["verified_at_sha"] = commit_sha
        wo["closed_at"] = datetime.now(timezone.utc).isoformat()
        wo["result"] = result

        done_path.write_text(yaml.dump(wo, sort_keys=False))
        ops_completed.append("write_result_yaml")

        # Operation 3: Remove running WO
        running_path.unlink()
        ops_completed.append("remove_running_yaml")

        # Operation 4: Remove lock (with validation)
        if lock_path.exists():
            lock_path.unlink()
        ops_completed.append("remove_lock")

        return Ok(None)

    except Exception as e:
        # Rollback based on what completed
        if "remove_running_yaml" in ops_completed:
            # Restore running YAML from result/
            if done_path.exists():
                running_path.write_text(done_path.read_text())
        if "write_result_yaml" in ops_completed and "remove_running_yaml" not in ops_completed:
            # Remove result YAML
            if done_path.exists():
                done_path.unlink()
        return Err(f"WO finish failed, rolled back: {e}")


# =============================================================================
# Main CLI
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finish a work order with artifact generation and validation"
    )
    parser.add_argument("wo_id", nargs="?", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument(
        "--result",
        choices=["done", "failed"],
        default=None,
        help="Final status of the WO",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate artifacts but don't move WO to done/",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean existing artifacts before regenerating",
    )
    parser.add_argument(
        "--skip-dod",
        action="store_true",
        help="Skip DoD validation (for emergency closures only)",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip WO verification gates (for emergency closures only)",
    )
    parser.add_argument(
        "--global-gate",
        action="store_true",
        help="Also run scripts/verify.sh global gate after scope gate",
    )
    args = parser.parse_args()

    if not args.wo_id:
        parser.print_help()
        return 0

    root_result = resolve_runtime_root(args.root)
    if root_result.is_err():
        err_msg = root_result.unwrap_err()
        print_error_card(
            error_code="INVALID_SEGMENT_PATH",
            error_class="VALIDATION",
            cause=err_msg or "unknown error",
            next_steps=[
                "Use a valid repository path with --root",
                "Run from repo root or pass --root /abs/path/to/repo",
            ],
            verify_cmd="python scripts/ctx_wo_finish.py WO-XXXX --root .",
        )
        return 1
    root = root_result.unwrap()
    assert root is not None, "root should be Path after successful resolution"

    running_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"
    if not running_path.exists():
        diagnostic = inspect_nonrunning_state(args.wo_id, root)
        if diagnostic:
            card_code = (
                "WO_STATE_CORRUPTED"
                if "Corrupted WO state detected" in diagnostic
                else "WO_NOT_RUNNING"
            )
            print_error_card(
                error_code=card_code,
                error_class="INTEGRITY",
                cause=diagnostic,
                next_steps=[
                    "Run: uv run python scripts/ctx_reconcile_state.py --root . --json /tmp/reconcile_wo.json",
                    f"Ensure {_ctx_running_path(args.wo_id, root)} exists before finish",
                ],
                verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
            )
            return 1
        print_error_card(
            error_code="WO_NOT_RUNNING",
            error_class="PRECONDITION",
            cause=f"missing WO {running_path}",
            next_steps=[
                "Take the WO first: python scripts/ctx_wo_take.py WO-XXXX",
                "Verify _ctx/jobs/running contains WO YAML",
            ],
            verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
        )
        return 1

    # Load WO and DOD catalog
    wo = load_yaml(running_path)
    if wo is None:
        print_error_card(
            error_code="WO_NOT_RUNNING",
            error_class="VALIDATION",
            cause=f"failed to load WO YAML from {running_path}",
            next_steps=[
                "Verify WO YAML file exists and is valid",
                "Run: uv run python scripts/ctx_reconcile_state.py --root . --json /tmp/reconcile_wo.json",
            ],
            verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
        )
        return 1
    dod_catalog = load_dod_catalog(root)
    dod_id = wo.get("dod_id")
    if not isinstance(dod_id, str):
        print_error_card(
            error_code="DOD_VALIDATION_FAILED",
            error_class="VALIDATION",
            cause=f"invalid dod_id type: {type(dod_id).__name__}",
            next_steps=[
                "Fix dod_id in WO YAML - must be a string",
                "Run: make wo-lint",
            ],
            verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
        )
        return 1
    dod = dod_catalog.get(dod_id)
    if not dod:
        print_error_card(
            error_code="DOD_VALIDATION_FAILED",
            error_class="VALIDATION",
            cause=f"unknown dod_id {dod_id}",
            next_steps=[
                "Fix dod_id in WO YAML or add DoD entry in _ctx/dod/*.yaml",
                "Run: make wo-lint",
            ],
            verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
        )
        return 1

    # Handle generate-only mode
    if args.generate_only:
        result = generate_artifacts(args.wo_id, root, clean=args.clean)
        if result.is_err():
            print(f"ERROR: {result.unwrap_err()}")
            return 1
        print(f"Artifacts generated: {result.unwrap()}")
        return 0

    # Validate DOD unless skipped
    if not args.skip_dod:
        dod_result = validate_minimum_evidence(args.wo_id, root)
        if dod_result.is_err():
            print_error_card(
                error_code="DOD_VALIDATION_FAILED",
                error_class="VALIDATION",
                cause=dod_result.unwrap_err() or "DoD validation failed",
                next_steps=[
                    f"Regenerate artifacts: python scripts/ctx_wo_finish.py {args.wo_id} --root {root} --generate-only --clean",
                    "Re-run with DoD enabled (without --skip-dod)",
                ],
                verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
            )
            return 1

    if not args.skip_verification:
        scope_result = run_scope_verification_gate(args.wo_id, root)
        if scope_result.is_err():
            print(f"ERROR: {scope_result.unwrap_err()}")
            return 1

        evidence_result = validate_session_evidence(args.wo_id, root)
        if evidence_result.is_err():
            evidence_err = evidence_result.unwrap_err() or "evidence validation failed"
            error_code = (
                "EVIDENCE_INVALID" if "EVIDENCE_INVALID" in evidence_err else "EVIDENCE_MISSING"
            )
            print(
                render_error_card(
                    error_code=error_code,
                    error_class="VALIDATION",
                    cause=evidence_err,
                    next_steps=[
                        "Add evidence entries to _ctx/session_trifecta_dope.md",
                        f"Expected: [{args.wo_id}] intent: ... and [{args.wo_id}] result: ...",
                    ],
                    verify_cmd=rf"grep -E \'\\[{args.wo_id}\\] (intent|result):\' _ctx/session_trifecta_dope.md",
                )
            )
            return 1

        verdict_result = validate_scope_verdict(args.wo_id, root)
        if verdict_result.is_err():
            print(f"ERROR: {verdict_result.unwrap_err()}")
            return 1

        report_result = write_scope_verification_report(args.wo_id, root)
        if report_result.is_err():
            print(f"ERROR: {report_result.unwrap_err()}")
            return 1

    if not args.skip_verification and args.global_gate:
        verify_result = run_verification_gate(args.wo_id, root)
        if verify_result.is_err():
            verify_cause = verify_result.unwrap_err() or "verification failed"
            card_code = (
                "VERIFY_SCRIPT_MISSING"
                if verify_cause.startswith("Verification script missing:")
                else "VERIFY_GATE_FAILED"
            )
            print_error_card(
                error_code=card_code,
                error_class="GATE",
                cause=verify_cause,
                next_steps=[
                    "Run verification directly: bash scripts/verify.sh WO-XXXX --root .",
                    "Fix failing blocking gates before retrying finish",
                ],
                verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
            )
            return 1

    # Finish WO as transaction
    result_status: Literal["done", "failed"] = args.result or "done"
    finish_result = finish_wo_transaction(args.wo_id, root, result_status)
    if finish_result.is_err():
        print_error_card(
            error_code="WO_NOT_RUNNING",
            error_class="TRANSACTION",
            cause=finish_result.unwrap_err() or "transaction failed",
            next_steps=[
                "Ensure git state is clean and branch is not detached HEAD",
                "Re-run finish command after resolving repository state",
            ],
            verify_cmd=f"python scripts/ctx_wo_finish.py {args.wo_id} --root {root}",
        )
        return 1

    # Post-finish hook for Sidecar integration.
    update_worktree_index(root)

    print(f"WO {args.wo_id} finished successfully (status: {result_status})")

    # Record in Trifecta Session Log
    try:
        summary = f"Finished Work Order {args.wo_id} (status: {result_status})"
        commands = f"ctx_wo_finish.py {args.wo_id} --result {result_status}"
        # Execute trifecta session append via subprocess
        import subprocess

        subprocess.run(
            [
                "uv",
                "run",
                "trifecta",
                "session",
                "append",
                "--segment",
                ".",
                "--summary",
                summary,
                "--commands",
                commands,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as e:
        logger.warning(f"Failed to append to session log: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
