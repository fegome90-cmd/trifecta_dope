#!/usr/bin/env bash
# =============================================================================
# repo_verify.sh - Repository-wide Hygiene Checks (CI-only)
# =============================================================================
#
# This script runs repo-wide checks that should NOT block WO closure:
# - WO YAML formatting (wo-fmt-check)
# - WO YAML linting (wo-lint)
# - verify.sh if it exists
#
# These checks are meant for CI pipelines, not for blocking WO closure.
# A WO should be able to close even if other WOs have formatting/lint issues.
#
# Usage:
#   bash scripts/repo_verify.sh [--root PATH]
#
# Exit codes:
#   0: All checks passed
#   1: One or more checks failed
#
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/repo_verify.sh [--root PATH]

Repository-wide hygiene checks (does NOT block WO closure):
  - WO YAML formatting (wo-fmt-check)
  - WO YAML linting (wo-lint)
  - verify.sh if it exists

These checks are for CI pipelines. WO closure uses wo_verify.sh instead.

Options:
  --root PATH       Repository root (default: .)

Examples:
  # Run all repo hygiene checks
  bash scripts/repo_verify.sh --root .

  # In CI pipeline
  bash scripts/repo_verify.sh && echo "Repo hygiene OK"
USAGE
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi

ROOT="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      if [[ -z ${2:-} ]]; then
        echo "ERROR: --root requires a path" >&2
        exit 2
      fi
      ROOT="$2"
      shift 2
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

ROOT="$(cd "$ROOT" && pwd)"
cd "$ROOT"

echo "=== Repository Hygiene Checks ==="
echo ""

# =============================================================================
# Check 1: WO YAML Formatting
# =============================================================================
echo "1. WO YAML Formatting (wo-fmt-check)..."
if uv run python scripts/ctx_wo_fmt.py --check 2>&1; then
  echo "   ✅ wo-fmt-check passed"
else
  echo "   ❌ wo-fmt-check failed"
  echo "   TIP: Run 'make wo-fmt' to auto-fix formatting issues"
  exit 1
fi

# =============================================================================
# Check 2: WO YAML Linting
# =============================================================================
echo "2. WO YAML Linting (wo-lint)..."
if uv run python scripts/ctx_wo_lint.py --strict 2>&1; then
  echo "   ✅ wo-lint passed"
else
  echo "   ❌ wo-lint failed"
  echo "   TIP: Fix linting errors in _ctx/jobs/ YAML files"
  exit 1
fi

# =============================================================================
# Check 3: verify.sh (if exists)
# =============================================================================
if [[ -f "verify.sh" ]]; then
  echo "3. verify.sh (custom)..."
  if bash verify.sh 2>&1; then
    echo "   ✅ verify.sh passed"
  else
    echo "   ❌ verify.sh failed"
    exit 1
  fi
else
  echo "3. verify.sh (skipped - not found)"
fi

echo ""
echo "=== All Repository Hygiene Checks Passed ==="
