#!/usr/bin/env bash
# =============================================================================
# ctx_verify_run.sh - Backward-compatible wrapper for wo_verify.sh
# =============================================================================
#
# This script is now a thin wrapper around wo_verify.sh (the SSOT).
# All verification logic has moved to wo_verify.sh for maintainability.
#
# For new code, prefer calling wo_verify.sh directly:
#   bash scripts/wo_verify.sh WO-0045 --root .
#
# For repo-wide hygiene checks, use repo_verify.sh:
#   bash scripts/repo_verify.sh --root .
#
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ctx_verify_run.sh <WO-ID> [--root PATH] [--allow-dirty]

WO Verification (wrapper for wo_verify.sh):
  - Runs scope lint in staged mode
  - Executes verify.commands from WO YAML
  - Writes verdict.json on success AND failure

Options:
  --root PATH       Repository root (default: .)
  --allow-dirty     Allow dirty worktree (prints warning)

Note: This is a backward-compatible wrapper. For new code, prefer:
  bash scripts/wo_verify.sh <WO-ID> --root .

For repo-wide hygiene (not WO-specific), use:
  bash scripts/repo_verify.sh --root .
USAGE
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

# Find the script directory to locate wo_verify.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Delegate to wo_verify.sh (SSOT)
exec bash "$SCRIPT_DIR/wo_verify.sh" "$@"
