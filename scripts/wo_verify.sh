#!/usr/bin/env bash
# =============================================================================
# wo_verify.sh - Single Source of Truth (SSOT) for WO Verification
# =============================================================================
#
# This is the authoritative WO verification script. It:
# 1. Runs scope lint in staged mode (what will be committed)
# 2. Loads verify.commands from WO YAML
# 3. Executes commands and writes verdict.json ALWAYS
# 4. Exits 1 on any failure
#
# IMPORTANT: This script does NOT run repo-wide checks (wo-fmt-check, wo-lint).
# Those belong in repo_verify.sh or CI pipelines.
#
# Usage:
#   bash scripts/wo_verify.sh <WO-ID> [--root PATH] [--allow-dirty]
#
# Exit codes:
#   0: All verification passed
#   1: Verification failed (scope violation, dirty tree, command failure)
#
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/wo_verify.sh <WO-ID> [--root PATH] [--allow-dirty]

WO Verification (SSOT):
  - Runs scope lint in staged mode
  - Executes verify.commands from WO YAML
  - Writes verdict.json on success AND failure

Options:
  --root PATH       Repository root (default: .)
  --allow-dirty     Allow dirty worktree (prints warning)

Environment:
  WILDCARD_POLICY   warn|enforce (default: enforce)

Examples:
  # Standard WO verification
  bash scripts/wo_verify.sh WO-0045 --root .

  # Allow dirty worktree for local development
  bash scripts/wo_verify.sh WO-0045 --root . --allow-dirty
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

WO_ID="$1"
shift

ROOT="."
ALLOW_DIRTY=""

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
    --allow-dirty)
      ALLOW_DIRTY="--allow-dirty"
      shift
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

ROOT="$(cd "$ROOT" && pwd)"
WO_PATH="$ROOT/_ctx/jobs/running/$WO_ID.yaml"
if [[ ! -f "$WO_PATH" ]]; then
  WO_PATH="$ROOT/_ctx/jobs/pending/$WO_ID.yaml"
fi
export WO_PATH

utc_now() {
  uv run python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
PY
}

write_verdict() {
  local status="$1"
  local failure_stage="${2:-}"
  local commands="${3:-}"
  if ! uv run python - "$status" "$failure_stage" "$commands" <<'PY' 2>&1
import json, os, sys
from pathlib import Path
import yaml

status = sys.argv[1]
failure_stage = sys.argv[2] if len(sys.argv) > 2 else ""
commands_str = sys.argv[3] if len(sys.argv) > 3 else ""

wo_path = Path(os.environ["WO_PATH"])
try:
    wo = yaml.safe_load(wo_path.read_text()) or {}
except:
    wo = {}

verdict = {
    "wo_id": wo.get("id", os.environ.get("WO_ID", "UNKNOWN")),
    "epic_id": wo.get("epic_id"),
    "dod_id": wo.get("dod_id"),
    "git_commit": os.popen(f"git -C '{os.environ.get('ROOT', '.')}' rev-parse HEAD").read().strip(),
    "status": status,
    "started_at": os.environ.get("START", ""),
    "finished_at": os.environ.get("END", ""),
    "commands": commands_str.split("\n") if commands_str else [],
}
if failure_stage:
    verdict["failure_stage"] = failure_stage

log_dir = Path(os.environ.get("LOG_DIR", "_ctx/logs"))
(log_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
PY
then
  echo "FATAL: Failed to write verdict.json for $WO_ID" >&2
  # Continue anyway to preserve original exit code
fi
}

if [[ ! -f "$WO_PATH" ]]; then
  echo "ERROR: missing WO $WO_PATH" >&2
  exit 1
fi

LOG_DIR="$ROOT/_ctx/logs/$WO_ID"
mkdir -p "$LOG_DIR"
export LOG_DIR ROOT WO_ID

# =============================================================================
# Step 1: Scope Lint (staged mode, fail-closed)
# =============================================================================
SCOPE_ARGS=("$WO_ID" "--root" "$ROOT" "--mode" "staged")
if [[ -n "$ALLOW_DIRTY" ]]; then
  SCOPE_ARGS+=("--allow-dirty")
fi

START="$(utc_now)"
export START

if ! uv run python "$ROOT/scripts/ctx_scope_lint.py" "${SCOPE_ARGS[@]}"; then
  echo "ERROR: Scope lint failed for $WO_ID" >&2
  END="$(utc_now)"
  export END
  write_verdict "FAIL" "scope_lint" ""
  exit 1
fi

# =============================================================================
# Step 2: Load verify.commands from WO YAML
# =============================================================================
COMMANDS_FILE="$LOG_DIR/commands.txt"
if ! uv run python - "$COMMANDS_FILE" <<'PY' 2>&1
import os, sys
from pathlib import Path
import yaml

commands_file = sys.argv[1]

try:
    wo_path = Path(os.environ["WO_PATH"])
    wo = yaml.safe_load(wo_path.read_text())
except (yaml.YAMLError, OSError) as exc:
    print(f"ERROR: failed to load verify.commands: {exc}", file=sys.stderr)
    sys.exit(1)

if wo is None or not isinstance(wo, dict):
    print("ERROR: failed to load verify.commands: invalid WO payload", file=sys.stderr)
    sys.exit(1)

commands = wo.get("verify", {}).get("commands", [])
if not commands:
    print("ERROR: verify.commands is empty", file=sys.stderr)
    sys.exit(1)

if not isinstance(commands, list) or not all(isinstance(cmd, str) for cmd in commands):
    print("ERROR: verify.commands must be a list of strings", file=sys.stderr)
    sys.exit(1)

Path(commands_file).write_text("\n".join(commands))
PY
then
  END="$(utc_now)"
  export END
  write_verdict "FAIL" "load_commands" ""
  exit 1
fi

# Read commands from file
mapfile -t COMMANDS < "$COMMANDS_FILE"

# =============================================================================
# Step 3: Execute verify.commands
# =============================================================================
STATUS="PASS"
INDEX=0
for CMD in "${COMMANDS[@]}"; do
  [[ -z "$CMD" ]] && continue
  INDEX=$((INDEX+1))
  LOG_FILE="$LOG_DIR/command_${INDEX}.log"
  if ! bash -lc "$CMD" >"$LOG_FILE" 2>&1; then
    STATUS="FAIL"
    break
  fi
done

END="$(utc_now)"
export END

# =============================================================================
# Step 4: Write verdict.json (ALWAYS, even on failure)
# =============================================================================
write_verdict "$STATUS" "" "$(printf '%s\n' "${COMMANDS[@]}")"

[[ "$STATUS" == "PASS" ]] || exit 1
