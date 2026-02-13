#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ctx_verify_run.sh <WO-ID> [--root PATH]
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
ROOT="."
if [[ ${2:-} == "--root" ]]; then
  if [[ -z ${3:-} ]]; then
    echo "ERROR: --root requires a path"
    exit 2
  fi
  ROOT="$3"
fi

ROOT="$(cd "$ROOT" && pwd)"
WO_PATH="$ROOT/_ctx/jobs/running/$WO_ID.yaml"
if [[ ! -f "$WO_PATH" ]]; then
  WO_PATH="$ROOT/_ctx/jobs/pending/$WO_ID.yaml"
fi
export WO_PATH

utc_now() {
  python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
PY
}

if [[ ! -f "$WO_PATH" ]]; then
  echo "ERROR: missing WO $WO_PATH"
  exit 1
fi

LOG_DIR="$ROOT/_ctx/logs/$WO_ID"
mkdir -p "$LOG_DIR"

if ! COMMANDS=$(python - <<'PY' 2>&1
import os
import sys
from pathlib import Path
import yaml

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
print("\n".join(commands))
PY
)
then
  echo "$COMMANDS" >&2
  exit 1
fi

python "$ROOT/scripts/ctx_scope_lint.py" "$WO_ID" --root "$ROOT"

STATUS="PASS"
START="$(utc_now)"

INDEX=0
while IFS= read -r CMD; do
  if [[ -z "$CMD" ]]; then
    continue
  fi
  INDEX=$((INDEX+1))
  LOG_FILE="$LOG_DIR/command_${INDEX}.log"
  if ! bash -lc "$CMD" >"$LOG_FILE" 2>&1; then
    STATUS="FAIL"
    break
  fi
done <<< "$COMMANDS"

END="$(utc_now)"

GIT_SHA=$(git -C "$ROOT" rev-parse HEAD)
if ! python - <<PY 2>&1
import json
from pathlib import Path
import yaml

try:
    wo = yaml.safe_load(Path("$WO_PATH").read_text())
except (yaml.YAMLError, OSError) as exc:
    raise SystemExit(f"ERROR: failed to write verdict.json: {exc}")

if wo is None or not isinstance(wo, dict):
    raise SystemExit("ERROR: failed to write verdict.json: invalid WO payload")

verdict = {
    "wo_id": wo.get("id"),
    "epic_id": wo.get("epic_id"),
    "dod_id": wo.get("dod_id"),
    "git_commit": "$GIT_SHA",
    "status": "$STATUS",
    "started_at": "$START",
    "finished_at": "$END",
    "commands": "$COMMANDS".split("\n"),
}
try:
    Path("$LOG_DIR/verdict.json").write_text(json.dumps(verdict, indent=2))
except OSError as exc:
    raise SystemExit(f"ERROR: failed to write verdict.json: {exc}")
PY
then
  exit 1
fi

if [[ "$STATUS" != "PASS" ]]; then
  exit 1
fi
