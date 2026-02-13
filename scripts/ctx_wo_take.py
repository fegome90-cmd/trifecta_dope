#!/usr/bin/env python3
"""
Work Order take script for trifecta_dope.
Automatically creates git worktrees with atomic locking.
"""

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import yaml
from jsonschema import validate

# Import helpers module
from helpers import (
    logger,
    create_worktree,
    get_branch_name,
    get_worktree_path,
    create_lock,
    check_lock_age,
    run_command,
    execute_rollback,
)

# Import domain entities
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from domain.wo_entities import WorkOrder, WOState, Priority
from domain.wo_transactions import Transaction, RollbackOperation, RollbackType


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def load_schema(root: Path, name: str):
    schema_path = root / "docs" / "backlog" / "schema" / name
    return json.loads(schema_path.read_text())


def get_completed_wo_ids(root: Path) -> set[str]:
    """
    Get set of completed WO IDs for dependency validation.

    Args:
        root: Repository root path

    Returns:
        Set of WO IDs that are in "done" state
    """
    done_dir = root / "_ctx" / "jobs" / "done"
    if not done_dir.exists():
        return set()

    return {path.stem for path in done_dir.glob("WO-*.yaml")}


def validate_dependencies_using_domain(wo_data: dict, root: Path) -> tuple[bool, str | None]:
    """
    Validate WO dependencies using the domain's validation logic.

    This function creates a WorkOrder entity and calls its validate_dependencies
    method, avoiding duplication of validation logic.

    Args:
        wo_data: WO YAML data
        root: Repository root path

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Legacy priority mapping for backward compatibility
    LEGACY_PRIORITY_MAP = {
        "p0": "critical",
        "p1": "high",
        "p2": "medium",
        "p3": "low",
        "P0": "critical",
        "P1": "high",
        "P2": "medium",
        "P3": "low",
    }

    # Convert string priority to Priority enum if needed
    priority_str = wo_data.get("priority", "medium")
    if isinstance(priority_str, str):
        # Map legacy priority values to new enum values
        normalized_priority = LEGACY_PRIORITY_MAP.get(priority_str, priority_str.lower())
        priority = Priority(normalized_priority)
    else:
        priority = priority_str

    # Convert dependencies list to tuple if needed
    deps_list = wo_data.get("dependencies", [])
    dependencies = tuple(deps_list) if isinstance(deps_list, list) else deps_list

    try:
        # Create WorkOrder entity (this validates structure via __post_init__)
        wo = WorkOrder(
            id=wo_data["id"],
            epic_id=wo_data.get("epic_id", ""),
            title=wo_data.get("title", ""),
            priority=priority,
            status=WOState(wo_data.get("status", "pending")),
            owner=wo_data.get("owner"),
            dod_id=wo_data.get("dod_id", ""),
            dependencies=dependencies,
            started_at=None,  # Not needed for dependency validation
            finished_at=None,
            branch=None,
            worktree=None,
        )
    except ValueError as e:
        return False, str(e)

    # Get completed WO IDs
    completed_ids = get_completed_wo_ids(root)

    # Use domain's validation method
    result = wo.validate_dependencies(completed_ids)

    if result.is_ok():
        return True, None
    else:
        error = result.unwrap_err()
        return False, error.message


def validate_execution_contract(wo_data: dict) -> tuple[bool, str | None]:
    """Validate mandatory Trifecta execution contract for WO."""
    execution = wo_data.get("execution")
    if not isinstance(execution, dict):
        return False, "execution contract is required"

    engine = execution.get("engine")
    if engine != "trifecta":
        return False, "engine must be 'trifecta'"

    segment = execution.get("segment")
    if segment != ".":
        return False, "segment must be '.'"

    required_flow = execution.get("required_flow")
    if not isinstance(required_flow, list) or not all(isinstance(step, str) for step in required_flow):
        return False, "required_flow must be a list of strings"

    mandatory_steps = [
        "session.append:intent",
        "ctx.sync",
        "ctx.search",
        "ctx.get",
        "session.append:result",
    ]
    missing = [step for step in mandatory_steps if step not in required_flow]
    if missing:
        return False, f"required_flow missing mandatory steps: {', '.join(missing)}"

    return True, None


def validate_wo_immediately(
    root: Path, wo_id: str, job_path: Path
) -> tuple[bool, list[dict[str, Any]]]:
    """Run fail-closed immediate validation for a specific WO."""
    repo_root = Path(__file__).resolve().parent.parent
    lint_script = Path(__file__).resolve().parent / "ctx_wo_lint.py"
    cmd = [
        "uv",
        "run",
        "python",
        str(lint_script),
        "--strict",
        "--json",
        "--wo-id",
        wo_id,
        "--root",
        str(root),
    ]
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    findings: list[dict[str, Any]] = []
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, list):
                findings = [f for f in parsed if isinstance(f, dict)]
            else:
                logger.error("Immediate WO validation returned invalid JSON payload type")
                return False, []
        except json.JSONDecodeError:
            logger.error("Immediate WO validation returned non-JSON output")
            if result.stderr:
                logger.error(result.stderr.strip())
            return False, []

    if result.returncode != 0:
        errors = [f for f in findings if f.get("severity") == "ERROR"]
        logger.error(f"Immediate WO validation failed for {wo_id}")
        if errors:
            for finding in errors[:10]:
                path_str = finding.get("path", "")
                path_suffix = f" {path_str}" if path_str else ""
                logger.error(
                    f"[ERROR] {finding.get('code', 'UNKNOWN')}{path_suffix}: "
                    f"{finding.get('message', 'unknown error')}"
                )
        else:
            logger.error("Immediate WO validation failed without structured findings")
            if result.stderr:
                logger.error(result.stderr.strip())
        logger.error("Run: make wo-fmt && make wo-lint")
        logger.error(f"Inspect: {job_path}")
        return False, findings

    return True, findings

def update_worktree_index(root: Path) -> None:
    """Regenerate `_ctx/index/wo_worktrees.json` via export_wo_index.py."""
    export_script = root / "scripts" / "export_wo_index.py"
    if not export_script.exists():
        logger.warning(f"Skipped index update: missing {export_script}")
        return
    try:
        subprocess.run(
            ["uv", "run", "python", str(export_script)],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("Updated worktree index via export_wo_index.py")
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning(f"Failed to update worktree index via export_wo_index.py: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Take a work order and create isolated worktree",
        epilog="""
Examples:
  python ctx_wo_take.py WO-0001           # Take WO-0001 (auto-generates branch & worktree)
  python ctx_wo_take.py WO-0001 --owner   # Take with current user as owner
  python ctx_wo_take.py --list            # List pending work orders
        """,
    )
    parser.add_argument("wo_id", nargs="?", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root (default: current directory)")
    parser.add_argument("--owner", default=None, help="Owner name (default: current user)")
    parser.add_argument("--list", action="store_true", help="List pending work orders")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip domain dependency validation only (schema/lint validation still enforced)",
    )
    args = parser.parse_args()

    # Handle --list flag
    if args.list:
        pending_dir = Path(args.root) / "_ctx" / "jobs" / "pending"
        if pending_dir.exists():
            wos = sorted(pending_dir.glob("WO-*.yaml"))
            if wos:
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("   Pending Work Orders")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                for wo_file in wos:
                    wo_data = load_yaml(wo_file)
                    priority = wo_data.get("priority", "?")
                    title = wo_data.get("title", wo_data.get("id", ""))
                    print(f"  {wo_file.stem} [{priority}] - {title}")
                print(f"\nTotal: {len(wos)}")
            else:
                print("No pending work orders found.")
        else:
            print(f"Pending directory not found: {pending_dir}")
        return 0

    # Handle --status flag
    if args.status:
        root = Path(args.root).resolve()
        jobs_dir = root / "_ctx" / "jobs"

        pending = (
            len(list((jobs_dir / "pending").glob("WO-*.yaml")))
            if (jobs_dir / "pending").exists()
            else 0
        )
        running = (
            len(list((jobs_dir / "running").glob("WO-*.yaml")))
            if (jobs_dir / "running").exists()
            else 0
        )
        done = (
            len(list((jobs_dir / "done").glob("WO-*.yaml"))) if (jobs_dir / "done").exists() else 0
        )
        failed = (
            len(list((jobs_dir / "failed").glob("WO-*.yaml")))
            if (jobs_dir / "failed").exists()
            else 0
        )

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("   System Status")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  Pending:   {pending}")
        print(f"  Running:   {running}")
        print(f"  Done:      {done}")
        print(f"  Failed:    {failed}")

        # Show active worktrees
        result = run_command(["git", "worktree", "list"], cwd=root, check=False)
        if result.returncode == 0:
            print("\nActive worktrees:")
            for line in result.stdout.splitlines()[1:]:  # Skip header
                print(f"  {line}")
        return 0

    if not args.wo_id:
        parser.print_help()
        return 0

    root = Path(args.root).resolve()
    wo_id = args.wo_id

    if not re.match(r"^WO-[A-Za-z0-9.-]+$", wo_id):
        logger.error(f"Invalid WO ID format: {wo_id} (expected: WO-<alphanumeric>)")
        return 1

    job_path = root / "_ctx" / "jobs" / "pending" / f"{wo_id}.yaml"
    if not job_path.exists():
        logger.error(f"Work order not found: {job_path}")
        return 1

    # Load and validate WO
    logger.info(f"Loading work order: {wo_id}")
    wo = load_yaml(job_path)

    schema = load_schema(root, "work_order.schema.json")
    try:
        validate(instance=wo, schema=schema)
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return 1

    execution_valid, execution_error = validate_execution_contract(wo)
    if not execution_valid:
        logger.error(f"Execution contract validation failed: {execution_error}")
        return 1

    # Validate epic_id
    backlog = load_yaml(root / "_ctx" / "backlog" / "backlog.yaml")
    epic_ids = {e.get("id") for e in backlog.get("epics", [])}
    if wo.get("epic_id") not in epic_ids:
        logger.error(f"Unknown epic_id: {wo.get('epic_id')}")
        return 1

    # Fail-closed immediate validation (does not bypass with --force)
    immediate_ok, _ = validate_wo_immediately(root, wo_id, job_path)
    if not immediate_ok:
        return 1

    # Validate dependencies using domain logic
    if not args.force:
        deps_valid, deps_error = validate_dependencies_using_domain(wo, root)
        if not deps_valid:
            logger.error(f"Dependency validation failed: {deps_error}")
            logger.error("Use --force to override (not recommended)")
            return 1
    else:
        logger.warning("Force mode enabled: skipping dependency validation")

    # Check for existing lock
    running_dir = root / "_ctx" / "jobs" / "running"
    running_dir.mkdir(parents=True, exist_ok=True)
    lock_path = running_dir / f"{wo_id}.lock"

    if lock_path.exists():
        if check_lock_age(lock_path, max_age_seconds=3600):
            logger.info(f"Found stale lock (>1 hour), removing: {lock_path}")
            lock_path.unlink()
        else:
            lock_content = lock_path.read_text()
            logger.error(f"Work order is locked: {wo_id}")
            logger.error(f"Lock info:\n{lock_content}")
            return 1

    # Initialize transaction (NEW)
    transaction = Transaction(wo_id=wo_id, operations=())

    try:
        # Step 1: Acquire lock
        logger.info(f"Acquiring lock for {wo_id}...")
        if not create_lock(lock_path, wo_id):
            logger.error("Failed to acquire lock")
            return 1

        logger.info(f"✓ Lock acquired: {lock_path}")
        transaction = transaction.add_operation(
            RollbackOperation(
                name="acquire_lock",
                description="Remove acquired lock",
                rollback_type=RollbackType.REMOVE_LOCK,
            )
        )

        # Step 2: Update WO metadata
        owner = args.owner or getpass.getuser()
        wo["owner"] = owner
        wo["status"] = "running"
        wo["started_at"] = datetime.now(timezone.utc).isoformat()

        # Auto-generate branch and worktree if not specified
        branch = wo.get("branch")
        worktree = wo.get("worktree")

        if branch is None or worktree is None:
            auto_branch = get_branch_name(wo_id)
            auto_worktree = get_worktree_path(wo_id, root)
            logger.info("Auto-generated configuration:")
            logger.info(f"  branch: {auto_branch}")
            logger.info(f"  worktree: {auto_worktree}")

            if branch is None:
                branch = auto_branch
                wo["branch"] = branch
            if worktree is None:
                # Worktree is outside repo - compute relative path from repo root
                # Path.relative_to() would fail since worktree is not under repo
                worktree = os.path.relpath(auto_worktree, root)
                logger.info(f"  worktree (relative to repo): {worktree}")
                wo["worktree"] = worktree

        # Step 3: Create worktree (WRAP WITH TRANSACTION)
        try:
            logger.info(f"Creating worktree for {wo_id}...")
            create_worktree(root, wo_id, branch, Path(worktree))

            # Add rollback operations
            transaction = transaction.add_operation(
                RollbackOperation(
                    name="create_worktree",
                    description=f"Remove worktree at {worktree}",
                    rollback_type=RollbackType.REMOVE_WORKTREE,
                )
            )
            transaction = transaction.add_operation(
                RollbackOperation(
                    name="create_branch",
                    description=f"Remove branch {branch}",
                    rollback_type=RollbackType.REMOVE_BRANCH,
                )
            )
        except Exception as e:
            logger.error(f"Failed to create worktree: {e}")
            logger.info("Executing rollback...")
            rollback_result = execute_rollback(transaction, root)
            if rollback_result.is_partial_failure:
                logger.error(f"✗ Rollback partially failed: {rollback_result.failed_ops}")
            else:
                logger.info("✓ Rollback completed")
            return 1

        # Step 4: Move WO to running (WRAP WITH TRANSACTION)
        running_path = running_dir / f"{wo_id}.yaml"

        transaction = transaction.add_operation(
            RollbackOperation(
                name="move_wo_running",
                description="Move WO back to pending and reset metadata",
                rollback_type=RollbackType.MOVE_WO_TO_PENDING,
            )
        )

        try:
            write_yaml(running_path, wo)
            job_path.unlink()
            logger.info(f"✓ Work order moved to running: {running_path}")
        except Exception as e:
            logger.error(f"Failed to move WO to running: {e}")
            logger.info("Executing rollback...")
            rollback_result = execute_rollback(transaction, root)
            if rollback_result.is_partial_failure:
                logger.error(f"✗ Rollback partially failed: {rollback_result.failed_ops}")
            else:
                logger.info("✓ Rollback completed")
            return 1

        # Commit transaction (all operations successful)
        transaction = transaction.commit()
        logger.info(f"✓ Transaction committed for WO {wo_id}")

        # Update worktree index for Sidecar integration
        update_worktree_index(root)

    except Exception as e:
        logger.error(f"Unexpected error during WO take: {e}")
        logger.info("Executing rollback...")
        rollback_result = execute_rollback(transaction, root)
        if not rollback_result.is_partial_failure:
            logger.info("✓ Rollback completed")
        else:
            logger.error(f"✗ Rollback partially failed: {rollback_result.failed_ops}")
        return 1

    # Success message
    print("\n" + "━" * 50)
    print(f"   ✅ Work Order {wo_id} Taken Successfully")
    print("━" * 50)
    print(f"  WO ID:     {wo_id}")
    print(f"  Branch:    {wo['branch']}")
    print(f"  Worktree:  {wo['worktree']}")
    print(f"  Owner:     {owner}")

    # Record in Trifecta Session Log
    try:
        summary = f"Taken Work Order {wo_id}"
        commands = f"ctx_wo_take.py {wo_id}"
        # Execute trifecta session append via subprocess
        subprocess.run(
            ["uv", "run", "trifecta", "session", "append", "--segment", ".", "--summary", summary, "--commands", commands],
            cwd=root,
            capture_output=True,
            text=True,
            check=False
        )
        logger.info(f"✓ Recorded take in Trifecta session log")
    except Exception as e:
        logger.warning(f"Failed to record in Trifecta session log: {e}")

    print("\nNext steps:")
    print(f"  1. cd {wo['worktree']}")
    print(f"  2. Start working on {wo_id}")
    print(f"  3. Run: python ctx_wo_finish.py {wo_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
