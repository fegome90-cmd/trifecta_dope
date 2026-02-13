#!/usr/bin/env bash
# verify.sh - Generic verification gate for Trifecta work orders
# Version: 1.2.1
# Created: 2026-02-10
# Updated: 2026-02-10 - Fixed script corruption + consistent gates + report handling
#
# Purpose: Run comprehensive test suite + validations for WO completion
# Usage: bash scripts/verify.sh [WO_ID] [--check-only] [--root PATH]
#
# Arguments:
#   WO_ID        - Work Order ID for report generation (optional)
#   --check-only - Skip report generation, only run checks
#   --root PATH  - Resolve and run from this repository root (worktree-safe)
#
# VERIFICATION GATE DEFINITION (11 gates):
#   1. Unit tests (pytest tests/unit/)
#   2. Integration tests (pytest tests/integration/)
#   3. Acceptance tests (pytest tests/acceptance/ -m "not slow")
#   4. Linting (ruff check)
#   5. Formatting (ruff format --check)
#   6. Type checking (mypy, optional)
#   7. Debug code scan (print/breakpoint/pdb) - BLOCKING
#   8. Sensitive files scan (git tracked) - BLOCKING
#   9. Untracked files check (git) - NON-BLOCKING WARN
#  10. Work Order hygiene (wo-fmt-check + wo-lint) - BLOCKING
#  11. Backlog validation (ctx_backlog_validate.py) - NON-BLOCKING WARN
#
# Additional (non-blocking info):
#   - Change size analysis (WARN if >1000 lines)
#
# Exit Codes:
#   0 - All gates passed
#   1 - One or more blocking gates failed
#   2 - Gates passed but warnings present

set -uo pipefail

# ============================================================
# Arguments
# ============================================================
WO_ID=""
CHECK_ONLY=false
ROOT="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=true
      shift
      ;;
    --root)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --root requires a path"
        exit 1
      fi
      ROOT="$2"
      shift 2
      ;;
    *)
      if [[ -z "$WO_ID" ]]; then
        WO_ID="$1"
      fi
      shift
      ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "ERROR: invalid root path: $ROOT"
  exit 1
fi

ROOT="$(cd "$ROOT" && pwd -P)"

# Resolve runtime root from git common-dir so WO artifacts are written to a
# single shared _ctx state even when invoked from a worktree.
TOPLEVEL="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || echo "$ROOT")"
COMMON_DIR="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
if [[ -n "$COMMON_DIR" ]]; then
  if [[ "$COMMON_DIR" != /* ]]; then
    COMMON_DIR="$TOPLEVEL/$COMMON_DIR"
  fi
  RUNTIME_ROOT="$(cd "$(dirname "$COMMON_DIR")" && pwd -P)"
else
  RUNTIME_ROOT="$ROOT"
fi

cd "$ROOT"

# ============================================================
# Report setup (optional)
# ============================================================
REPORT_FILE=""
if [[ -n "$WO_ID" && "$CHECK_ONLY" == false ]]; then
  HANDOFF_DIR="${RUNTIME_ROOT}/_ctx/handoff/${WO_ID}"
  mkdir -p "$HANDOFF_DIR"
  REPORT_FILE="${HANDOFF_DIR}/verification_report.log"
  # Mirror output to console + file
  exec > >(tee "$REPORT_FILE") 2>&1
fi

# ============================================================
# UI Helpers
# ============================================================
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

section() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "$1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

pass() { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
skip() { echo -e "${YELLOW}⏭️ $1${NC}"; }

# ============================================================
# State Management
# ============================================================
EXIT_CODE=0
WARN_COUNT=0

set_fail() { EXIT_CODE=1; }
set_warn() { WARN_COUNT=$((WARN_COUNT + 1)); }

in_git_repo() {
  git rev-parse --git-dir >/dev/null 2>&1
}

# ============================================================
# Header
# ============================================================
echo "🔍 Trifecta Work Order Verification Gate"
echo "========================================"
[[ -n "$WO_ID" ]] && echo "Work Order: $WO_ID"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Fast deterministic mode for unit tests only.
if [[ "${TRIFECTA_VERIFY_SELFTEST:-0}" == "1" ]]; then
  echo "Self-test mode enabled, skipping verification gates."
  exit 0
fi

# ============================================================
# Gate 1: Unit Tests (BLOCKING)
# ============================================================
section "📋 Step 1/11: Unit Tests"
if uv run pytest -q tests/unit/; then
  pass "Unit tests passed"
else
  fail "Unit tests failed"
  set_fail
fi
echo ""

# ============================================================
# Gate 2: Integration Tests (BLOCKING)
# ============================================================
section "🔗 Step 2/11: Integration Tests"
if uv run pytest -q tests/integration/; then
  pass "Integration tests passed"
else
  fail "Integration tests failed"
  set_fail
fi
echo ""

# ============================================================
# Gate 3: Acceptance Tests (BLOCKING)
# ============================================================
section "🎯 Step 3/11: Acceptance Tests (fast)"
if uv run pytest -q tests/acceptance/ -m "not slow"; then
  pass "Acceptance tests passed"
else
  fail "Acceptance tests failed"
  set_fail
fi
echo ""

# ============================================================
# Gate 4: Linting (BLOCKING)
# ============================================================
section "🔍 Step 4/11: Linting (ruff check)"
if uv run ruff check src/ tests/; then
  pass "Linting passed"
else
  fail "Linting failed"
  set_fail
fi
echo ""

# ============================================================
# Gate 5: Formatting (BLOCKING)
# ============================================================
section "🎨 Step 5/11: Formatting (ruff format --check)"
if uv run ruff format --check src/ tests/; then
  pass "Formatting passed"
else
  fail "Formatting failed"
  echo -e "${YELLOW}    Fix with: uv run ruff format src/ tests/${NC}"
  set_fail
fi
echo ""

# ============================================================
# Gate 6: Type Checking (BLOCKING if configured, else SKIP)
# ============================================================
section "🧠 Step 6/11: Type Checking (mypy)"
if command -v mypy >/dev/null 2>&1 && [[ -f "pyproject.toml" ]]; then
  if uv run mypy --config-file pyproject.toml src/; then
    pass "Type checking passed"
  else
    fail "Type checking failed"
    set_fail
  fi
else
  skip "mypy not available or no pyproject.toml (SKIP)"
fi
echo ""

# ============================================================
# Gate 7: Debug Code Scan (BLOCKING)
# Decision: BLOCKING because it's a gate that catches real issues.
# If you want this as WARN, change set_fail → set_warn.
# ============================================================
section "🐛 Step 7/11: Debug Code Scan"
# Exclude tests/ by default; adjust pattern if stricter needed.
# Also exclude print statements with emojis (UI output like ✅, ❌, ⚠️)
DEBUG_PATTERN='(^|[^A-Za-z0-9_])(print\s*\(|breakpoint\s*\(|pdb\.set_trace\s*\()'
DEBUG_HITS="$(grep -RIn --include="*.py" -E "$DEBUG_PATTERN" src/ 2>/dev/null | grep -vE '✅|❌|⚠️|⏭️|🔍|📋|🔗|🎯|🎨|🧠|🐛|🔒|📁|📊|ℹ️' || true)"

if [[ -z "$DEBUG_HITS" ]]; then
  pass "No debug code found in src/"
else
  DEBUG_COUNT="$(echo "$DEBUG_HITS" | wc -l | tr -d ' ')"
  fail "Debug code found in src/: ${DEBUG_COUNT} hit(s)"
  echo "$DEBUG_HITS" | head -50
  set_fail
fi
echo ""

# ============================================================
# Gate 8: Sensitive Files Scan (BLOCKING)
# Prevents accidental commit of .env, secrets, credentials.
# ============================================================
section "🔒 Step 8/11: Sensitive Files Scan"
SENSITIVE_IN_GIT=false
SENSITIVE_FILES=(
  ".env"
  ".env.local"
  ".env.production"
  "secrets.json"
  "secrets.yaml"
  "secrets.yml"
  "config/production.json"
  "config/production.yaml"
  "config/production.yml"
)

if in_git_repo; then
  for file in "${SENSITIVE_FILES[@]}"; do
    if [[ -f "$file" ]] && git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
      fail "Sensitive file tracked in git: $file"
      SENSITIVE_IN_GIT=true
      set_fail
    fi
  done

  if [[ "$SENSITIVE_IN_GIT" == false ]]; then
    pass "No sensitive files tracked in git"
  fi
else
  skip "Not a git repository (SKIP)"
fi
echo ""

# ============================================================
# Gate 9: Untracked Files (NON-BLOCKING WARN)
# Flags build artifacts, temp files, etc. not .gitignore'd.
# ============================================================
section "📁 Step 9/11: Untracked Files"
if in_git_repo; then
  UNTRACKED="$(git ls-files --others --exclude-standard || true)"
  if [[ -z "$UNTRACKED" ]]; then
    pass "No untracked files"
  else
    UNTRACKED_COUNT="$(echo "$UNTRACKED" | grep -c . || true)"
    warn "${UNTRACKED_COUNT} untracked file(s) found"
    echo "First 10 files:"
    echo "$UNTRACKED" | head -10
    set_warn
  fi
else
  skip "Not a git repository (SKIP)"
fi
echo ""

# ============================================================
# Gate 10: Work Order Hygiene (BLOCKING)
# Fail-closed for WO consistency.
# ============================================================
section "🧷 Step 10/11: Work Order Hygiene"
if make wo-fmt-check && make wo-lint; then
  pass "Work Order hygiene passed"
else
  fail "Work Order hygiene failed"
  set_fail
fi
echo ""

# ============================================================
# Gate 11: Backlog Validation (NON-BLOCKING WARN)
# Decision: By design non-blocking to allow structural issues
# during development. If should FAIL on errors, change set_warn → set_fail.
# ============================================================
section "📊 Step 11/11: Backlog Validation"
if uv run python3 scripts/ctx_backlog_validate.py --strict; then
  pass "Backlog validation passed"
else
  warn "Backlog validation warnings (non-blocking)"
  set_warn
fi
echo ""

# ============================================================
# Additional: Change Size Analysis (NON-BLOCKING INFO)
# ============================================================
section "📊 Additional Info: Change Size Analysis"
if in_git_repo; then
  BASE_REF="${VALIDATOR_BASE_REF:-main}"

  if git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
    DIFF_OUTPUT="$(git diff --numstat "$BASE_REF" 2>/dev/null || true)"
    if [[ -n "$DIFF_OUTPUT" ]]; then
      ADDED="$(echo "$DIFF_OUTPUT" | awk '{sum+=$1} END {print sum+0}')"
      DELETED="$(echo "$DIFF_OUTPUT" | awk '{sum+=$2} END {print sum+0}')"
      TOTAL="$((ADDED + DELETED))"

      if [[ "$TOTAL" -gt 1000 ]]; then
        warn "Large change detected: +$ADDED -$DELETED (total: $TOTAL lines)"
        echo "    Consider breaking into smaller PRs for easier review"
        set_warn
      else
        pass "Change size reasonable: +$ADDED -$DELETED (total: $TOTAL lines)"
      fi
    else
      echo -e "${YELLOW}ℹ️  No changes detected against $BASE_REF${NC}"
    fi
  else
    echo -e "${YELLOW}ℹ️  Base ref '$BASE_REF' not found, skipping diff${NC}"
  fi
else
  skip "Not a git repository (SKIP)"
fi
echo ""

# ============================================================
# Final Summary + Exit Code Decision
# ============================================================
section "✅ Summary"
if [[ "$EXIT_CODE" -eq 0 ]]; then
  if [[ "$WARN_COUNT" -gt 0 ]]; then
    warn "VERIFICATION GATE PASSED WITH WARNINGS"
    echo "$WARN_COUNT warning(s) found - review recommended"
    EXIT_CODE=2
  else
    pass "VERIFICATION GATE PASSED"
    echo "All gates passed successfully"
  fi
else
  fail "VERIFICATION GATE FAILED"
  echo "One or more blocking gates failed - see output above"
fi

if [[ -n "$REPORT_FILE" ]]; then
  echo ""
  echo "Report saved to: $REPORT_FILE"
fi

exit "$EXIT_CODE"
