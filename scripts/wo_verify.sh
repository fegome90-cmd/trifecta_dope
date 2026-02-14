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

# =============================================================================
# Override Accountability Check
# =============================================================================
if [[ -n "$ALLOW_DIRTY" ]]; then
  if [[ -z "${OVERRIDE_REASON:-}" ]]; then
    echo "ERROR: --allow-dirty requires OVERRIDE_REASON environment variable" >&2
    exit 2
  fi
  if [[ ${#OVERRIDE_REASON} -lt 10 ]]; then
    echo "ERROR: OVERRIDE_REASON must be at least 10 characters (got ${#OVERRIDE_REASON})" >&2
    exit 2
  fi
  if [[ -z "${OVERRIDE_WO:-}" ]]; then
    echo "ERROR: --allow-dirty requires OVERRIDE_WO environment variable" >&2
    exit 2
  fi
  if [[ ! "$OVERRIDE_WO" =~ ^WO-[A-Za-z0-9.-]+$ ]]; then
    echo "ERROR: OVERRIDE_WO must match format WO-[A-Za-z0-9.-]+ (got ${OVERRIDE_WO:-none})" >&2
    exit 2
  fi
  if [[ -z "${OVERRIDE_UNTIL:-}" ]]; then
    echo "ERROR: --allow-dirty requires OVERRIDE_UNTIL environment variable (YYYY-MM-DD)" >&2
    exit 2
  fi
  if [[ ! "$OVERRIDE_UNTIL" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "ERROR: OVERRIDE_UNTIL must be YYYY-MM-DD (got $OVERRIDE_UNTIL)" >&2
    exit 2
  fi
  
  # Validate that OVERRIDE_UNTIL is a real calendar date
  if ! OVERRIDE_UNTIL_EPOCH=$(date -d "$OVERRIDE_UNTIL" +%s 2>/dev/null); then
    echo "ERROR: OVERRIDE_UNTIL is not a valid calendar date (got $OVERRIDE_UNTIL)" >&2
    exit 2
  fi
  
  # Validate expiry using epoch comparison
  TODAY=$(date +"%Y-%m-%d")
  TODAY_EPOCH=$(date -d "$TODAY" +%s)
  if (( OVERRIDE_UNTIL_EPOCH < TODAY_EPOCH )); then
    echo "ERROR: OVERRIDE_UNTIL ($OVERRIDE_UNTIL) has expired (today: $TODAY)" >&2
    exit 2
  fi

  echo "WARNING: Proceeding with dirty worktree (OVERRIDE: $OVERRIDE_WO until $OVERRIDE_UNTIL)" >&2
fi

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
import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone
import yaml

status = sys.argv[1]
failure_stage = sys.argv[2] if len(sys.argv) > 2 else ""
commands_str = sys.argv[3] if len(sys.argv) > 3 else ""

wo_path_env = os.environ.get("WO_PATH")
wo_path = Path(wo_path_env) if wo_path_env else None
wo = {}
if wo_path and wo_path.exists():
    try:
        wo = yaml.safe_load(wo_path.read_text()) or {}
    except:
        pass

started_at = os.environ.get("START", "")
finished_at = os.environ.get("END", "")

duration = 0.0
if started_at and finished_at:
    try:
        start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        duration = (end_dt - start_dt).total_seconds()
    except:
        pass

# Get git commit SHA safely
root = os.environ.get("ROOT", ".")
git_commit = ""
try:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    git_commit = result.stdout.strip()
except Exception:
    pass

verdict = {
    "schema_version": "1.0.0",
    "wo_id": wo.get("id", os.environ.get("WO_ID", "UNKNOWN")),
    "epic_id": wo.get("epic_id"),
    "dod_id": wo.get("dod_id"),
    "git_commit": git_commit,
    "status": status,
    "started_at": started_at,
    "finished_at": finished_at,
    "duration_seconds": duration,
    "commands": commands_str.split("\n") if commands_str else [],
}
if failure_stage:
    verdict["failure_stage"] = failure_stage

# Record override accountability metadata only when --allow-dirty is active
allow_dirty = os.environ.get("ALLOW_DIRTY")
override_reason = os.environ.get("OVERRIDE_REASON")
override_wo = os.environ.get("OVERRIDE_WO")
override_until = os.environ.get("OVERRIDE_UNTIL")
if allow_dirty and override_reason and override_wo and override_until:
    verdict["override"] = {
        "dirty": True,
        "reason": override_reason,
        "wo": override_wo,
        "until": override_until,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

log_dir_env = os.environ.get("LOG_DIR")
if log_dir_env:
    log_dir = Path(log_dir_env)
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "verdict.json").write_text(json.dumps(verdict, indent=2))
else:
    # Use default relative if somehow missing
    Path("_ctx/logs").mkdir(parents=True, exist_ok=True)
    Path("_ctx/logs/verdict.json").write_text(json.dumps(verdict, indent=2))
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

# Cleanup trap: Write verdict on crash (catchable signals only)
# SIGKILL cannot be caught - this is a Unix limitation
cleanup() {
  local exit_code=$?
  # Ensure LOG_DIR path is computed if possible
  if [[ -z "${LOG_DIR:-}" && -n "${ROOT:-}" && -n "${WO_ID:-}" ]]; then
    LOG_DIR="$ROOT/_ctx/logs/$WO_ID"
  fi
  
  if [[ -n "${LOG_DIR:-}" && ! -f "$LOG_DIR/verdict.json" ]]; then
    # Only try to write if we have the minimum context
    END="$(utc_now)"
    export END
    write_verdict "CRASH" "unexpected_exit" ""
  fi
  exit $exit_code
}
trap cleanup EXIT TERM INT HUP

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
