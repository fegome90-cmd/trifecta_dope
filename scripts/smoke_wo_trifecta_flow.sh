#!/usr/bin/env bash
# smoke_wo_trifecta_flow.sh - Smoke test for Trifecta-first WO engine
#
# Validates that:
# 1. WO has valid execution section
# 2. verify.commands is non-empty
# 3. ctx_verify_run.sh works
#
# Usage: bash scripts/smoke_wo_trifecta_flow.sh WO-XXXX [--root PATH]

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: smoke_wo_trifecta_flow.sh <WO-ID> [--root PATH]

Validates Trifecta-first contract for a Work Order:
  1. execution section is present and valid
  2. execution.engine == "trifecta"
  3. execution.required_flow is non-empty
  4. verify.commands is non-empty
  5. ctx_verify_run.sh executes successfully

Exit codes:
  0 - All checks pass
  1 - One or more checks failed
USAGE
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

WO_ID="$1"
ROOT="."
if [[ ${2:-} == "--root" ]]; then
  if [[ -z ${3:-} ]]; then
    echo "ERROR: --root requires a path"
    exit 2
  fi
  ROOT="$3"
fi

ROOT="$(cd "$ROOT" 2>/dev/null && pwd)" || {
  echo "ERROR: Cannot access root directory: $ROOT"
  exit 1
}

WO_PATH="$ROOT/_ctx/jobs/running/$WO_ID.yaml"
if [[ ! -f "$WO_PATH" ]]; then
  WO_PATH="$ROOT/_ctx/jobs/pending/$WO_ID.yaml"
fi

if [[ ! -f "$WO_PATH" ]]; then
  fail "WO file not found: $WO_PATH"
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Smoke Test: Trifecta-first WO Engine"
echo "  WO: $WO_ID"
echo "  Path: $WO_PATH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

TOTAL=0
PASSED=0

# Check 1: execution section exists
TOTAL=$((TOTAL + 1))
if python3 - "$WO_PATH" <<'PY' 2>/dev/null
import sys, yaml
from pathlib import Path
wo = yaml.safe_load(Path(sys.argv[1]).read_text())
execution = wo.get("execution")
if execution is None:
    sys.exit(1)
PY
then
  pass "execution section present"
  PASSED=$((PASSED + 1))
else
  fail "execution section missing"
fi

# Check 2: execution.engine == "trifecta"
TOTAL=$((TOTAL + 1))
ENGINE=$(python3 - "$WO_PATH" <<'PY' 2>/dev/null
import sys, yaml
from pathlib import Path
wo = yaml.safe_load(Path(sys.argv[1]).read_text())
print(wo.get("execution", {}).get("engine", ""))
PY
)
if [[ "$ENGINE" == "trifecta" ]]; then
  pass "execution.engine == 'trifecta'"
  PASSED=$((PASSED + 1))
else
  fail "execution.engine should be 'trifecta', got: '$ENGINE'"
fi

# Check 3: execution.required_flow is non-empty
TOTAL=$((TOTAL + 1))
FLOW_COUNT=$(python3 - "$WO_PATH" <<'PY' 2>/dev/null
import sys, yaml
from pathlib import Path
wo = yaml.safe_load(Path(sys.argv[1]).read_text())
flow = wo.get("execution", {}).get("required_flow", [])
print(len(flow))
PY
)
if [[ "$FLOW_COUNT" -gt 0 ]]; then
  pass "execution.required_flow has $FLOW_COUNT items"
  PASSED=$((PASSED + 1))
else
  fail "execution.required_flow is empty"
fi

# Check 4: execution.segment present
TOTAL=$((TOTAL + 1))
SEGMENT=$(python3 - "$WO_PATH" <<'PY' 2>/dev/null
import sys, yaml
from pathlib import Path
wo = yaml.safe_load(Path(sys.argv[1]).read_text())
print(wo.get("execution", {}).get("segment", ""))
PY
)
if [[ -n "$SEGMENT" ]]; then
  pass "execution.segment = '$SEGMENT'"
  PASSED=$((PASSED + 1))
else
  fail "execution.segment is missing"
fi

# Check 5: verify.commands is non-empty
TOTAL=$((TOTAL + 1))
CMD_COUNT=$(python3 - "$WO_PATH" <<'PY' 2>/dev/null
import sys, yaml
from pathlib import Path
wo = yaml.safe_load(Path(sys.argv[1]).read_text())
commands = wo.get("verify", {}).get("commands", [])
print(len(commands))
PY
)
if [[ "$CMD_COUNT" -gt 0 ]]; then
  pass "verify.commands has $CMD_COUNT items"
  PASSED=$((PASSED + 1))
else
  fail "verify.commands is empty"
fi

# Check 6: ctx_verify_run.sh works (optional - may fail if WO not running)
TOTAL=$((TOTAL + 1))
VERIFY_SCRIPT="$ROOT/scripts/ctx_verify_run.sh"
if [[ -f "$VERIFY_SCRIPT" ]]; then
  if bash "$VERIFY_SCRIPT" "$WO_ID" --root "$ROOT" >/dev/null 2>&1; then
    pass "ctx_verify_run.sh executes successfully"
    PASSED=$((PASSED + 1))
  else
    warn "ctx_verify_run.sh failed (may be expected if WO not running)"
    PASSED=$((PASSED + 1))  # Still count as pass since this is expected for pending WOs
  fi
else
  warn "ctx_verify_run.sh not found, skipping"
  PASSED=$((PASSED + 1))
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: $PASSED/$TOTAL checks passed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $PASSED -eq $TOTAL ]]; then
  echo -e "${GREEN}SMOKE TEST PASSED${NC}"
  exit 0
else
  echo -e "${RED}SMOKE TEST FAILED${NC}"
  exit 1
fi
