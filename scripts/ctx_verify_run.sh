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

if [[ ! -f "$WO_PATH" ]]; then
  echo "ERROR: missing WO $WO_PATH"
  exit 1
fi

LOG_DIR="$ROOT/_ctx/logs/$WO_ID"
mkdir -p "$LOG_DIR"

COMMANDS=$(python - <<'PY'
import json
import os
import sys
from pathlib import Path
import yaml

wo_path = Path(os.environ["WO_PATH"])
wo = yaml.safe_load(wo_path.read_text())
commands = wo.get("verify", {}).get("commands", [])
if not commands:
    print("ERROR: verify.commands is empty")
    sys.exit(1)
print("\n".join(commands))
PY
)

if [[ "$COMMANDS" == ERROR:* ]]; then
  echo "$COMMANDS"
  exit 1
fi

python "$ROOT/scripts/ctx_scope_lint.py" "$WO_ID" --root "$ROOT"

STATUS="PASS"
START=$(python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
PY
)

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

END=$(python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
PY
)

GIT_SHA=$(git -C "$ROOT" rev-parse HEAD)
python - <<PY
import json
import os
from pathlib import Path
import yaml

wo = yaml.safe_load(Path("$WO_PATH").read_text())
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
Path("$LOG_DIR/verdict.json").write_text(json.dumps(verdict, indent=2))
PY

if [[ "$STATUS" != "PASS" ]]; then
  exit 1
fi
