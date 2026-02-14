#!/usr/bin/env python3
"""
Scope linter for WO changes.

Modes:
  --mode staged (default): Only check staged files (what will be committed)
  --mode all: Check staged + unstaged + untracked (legacy mode)

Dirty worktree handling:
  --require-clean (default ON): Fail if working tree has unstaged/untracked changes
  --allow-dirty: Allow dirty working tree (prints warning, exits 0 if scope OK)

Exit codes and messages:
  0: All OK
  1: SCOPE_VIOLATIONS: + list
     DIRTY_WORKTREE_BLOCKS_CLOSE: + list (with --require-clean)
     WILDCARD_REQUIRES_OVERRIDE: (A4)
     OVERRIDE_EXPIRED: (A4)
"""
import argparse
import fnmatch
from datetime import date
from pathlib import Path
import subprocess
import sys
import os
import yaml


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text())
    except (yaml.YAMLError, OSError) as exc:
        raise SystemExit(f"ERROR: failed to load WO YAML: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("ERROR: WO YAML must be a mapping")
    return data


def get_staged_paths(root: Path) -> list[str]:
    """Get files that are staged for commit (git diff --cached)."""
    p = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"ERROR: git diff --cached failed: {p.stderr.strip()}")
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def get_unstaged_paths(root: Path) -> list[str]:
    """Get files with unstaged modifications (git diff, not --cached)."""
    p = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"ERROR: git diff failed: {p.stderr.strip()}")
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def get_untracked_paths(root: Path) -> list[str]:
    """Get untracked files (git ls-files --others)."""
    p = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"ERROR: git ls-files failed: {p.stderr.strip()}")
    return [line.strip() for line in p.stdout.splitlines() if line.strip()]


def get_dirty_paths(root: Path) -> list[str]:
    """Get all dirty paths (unstaged + untracked)."""
    return sorted(set(get_unstaged_paths(root) + get_untracked_paths(root)))


def get_all_paths(root: Path) -> list[str]:
    """Get all changed paths (staged + unstaged + untracked). Legacy mode."""
    staged = get_staged_paths(root)
    unstaged = get_unstaged_paths(root)
    untracked = get_untracked_paths(root)
    return sorted(set(staged + unstaged + untracked))


def is_denied(path: str, deny: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in deny)


def is_allowed(path: str, allow: list[str], deny: list[str]) -> bool:
    # Deny always wins (fail-closed)
    if is_denied(path, deny):
        return False

    # No allow list => deny everything
    if not allow:
        return False

    # Fast-path: global allow patterns
    if any(pat in ("*", "**/*", "*/**") for pat in allow):
        return True

    # Normal match
    for pat in allow:
        if fnmatch.fnmatch(path, pat):
            return True
        # support prefix-ish patterns like "dir/**"
        if pat.endswith("/**") and path.startswith(pat[:-3]):
            return True

    return False


def has_wildcard_allow(allow: list[str]) -> bool:
    """Check if scope.allow contains global wildcard patterns."""
    return any(pat in ("*", "**/*", "*/**") for pat in allow)


def validate_wildcard_override(scope: dict, enforce: bool) -> tuple[bool, str]:
    """
    Validate that wildcard allow has proper override documentation.

    Returns (is_valid, error_message).
    If enforce=False (warn mode), returns (True, warning_message).
    """
    allow = scope.get("allow", []) or []

    if not has_wildcard_allow(allow):
        return True, ""

    override = scope.get("override", False)
    override_reason = scope.get("override_reason", "")
    override_expires = scope.get("override_expires", "")

    # Check required fields
    if not override:
        msg = "WILDCARD_REQUIRES_OVERRIDE: scope.allow contains wildcard (*) but scope.override is not true"
        if not enforce:
            return True, f"WARNING: {msg}"
        return False, msg

    if len(override_reason) < 20:
        msg = f"WILDCARD_REQUIRES_OVERRIDE: scope.override_reason must be >= 20 chars (got {len(override_reason)})"
        if not enforce:
            return True, f"WARNING: {msg}"
        return False, msg

    if not override_expires:
        msg = "WILDCARD_REQUIRES_OVERRIDE: scope.override_expires is required when using wildcard"
        if not enforce:
            return True, f"WARNING: {msg}"
        return False, msg

    # Check expiration
    try:
        expires_date = date.fromisoformat(override_expires)
        if date.today() > expires_date:
            msg = f"OVERRIDE_EXPIRED: scope.override_expires ({override_expires}) is in the past"
            return False, msg
    except ValueError:
        msg = f"OVERRIDE_EXPIRED: scope.override_expires '{override_expires}' is not a valid ISO date (YYYY-MM-DD)"
        if not enforce:
            return True, f"WARNING: {msg}"
        return False, msg

    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scope linter for WO changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: check staged files, require clean worktree
  scripts/ctx_scope_lint.py WO-0001 --root .

  # Check all changes (legacy mode)
  scripts/ctx_scope_lint.py WO-0001 --root . --mode all

  # Allow dirty worktree (local development)
  scripts/ctx_scope_lint.py WO-0001 --root . --allow-dirty
        """,
    )
    parser.add_argument("wo_id", help="Work order id, e.g. WO-0001")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument(
        "--mode",
        choices=["staged", "all"],
        default="staged",
        help="staged: only staged files (default); all: staged + unstaged + untracked",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        dest="require_clean",
        default=True,
        help="Fail if working tree has unstaged/untracked changes (default: True)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        dest="allow_dirty",
        default=False,
        help="Allow dirty working tree (prints warning instead of failing)",
    )
    args = parser.parse_args()

    # --allow-dirty overrides --require-clean
    require_clean = args.require_clean and not args.allow_dirty

    root = Path(args.root).resolve()

    wo_path = root / "_ctx" / "jobs" / "running" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        wo_path = root / "_ctx" / "jobs" / "pending" / f"{args.wo_id}.yaml"
    if not wo_path.exists():
        print(f"ERROR: missing WO {wo_path}", file=sys.stderr)
        return 1

    wo = load_yaml(wo_path)
    scope = wo.get("scope", {}) or {}
    allow = scope.get("allow", []) or []
    deny = scope.get("deny", []) or []

    # A4: Check wildcard policy
    wildcard_policy = os.environ.get("WILDCARD_POLICY", "enforce")
    enforce_wildcard = wildcard_policy == "enforce"

    is_valid, wildcard_msg = validate_wildcard_override(scope, enforce_wildcard)
    if wildcard_msg:
        print(wildcard_msg, file=sys.stderr)
    if not is_valid:
        return 1

    # Check dirty worktree first (before scope check)
    if require_clean:
        dirty_paths = get_dirty_paths(root)
        if dirty_paths:
            print("DIRTY_WORKTREE_BLOCKS_CLOSE:")
            for p in dirty_paths:
                print(f"  {p}")
            print("", file=sys.stderr)
            print("TIP: Use --allow-dirty to bypass (not recommended for CI)", file=sys.stderr)
            return 1

    # Get paths based on mode
    if args.mode == "staged":
        paths_to_check = get_staged_paths(root)
    else:
        paths_to_check = get_all_paths(root)

    # If allow-dirty and there are dirty paths, print warning
    if args.allow_dirty:
        dirty_paths = get_dirty_paths(root)
        if dirty_paths:
            print("DIRTY_WORKTREE_ALLOWED:", file=sys.stderr)
            for p in dirty_paths:
                print(f"  {p}", file=sys.stderr)

    # Check scope violations
    violations: list[str] = []
    for path in paths_to_check:
        if not is_allowed(path, allow, deny):
            violations.append(path)

    if violations:
        print("SCOPE_VIOLATIONS:")
        for v in violations:
            print(v)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
