#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ctx_handoff_pack.sh <WO-ID> [--root PATH]
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

HANDOFF_DIR="$ROOT/_ctx/handoff/$WO_ID"
mkdir -p "$HANDOFF_DIR"

# Core git artifacts
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$ROOT" diff > "$HANDOFF_DIR/diff.patch"
  git -C "$ROOT" diff --stat > "$HANDOFF_DIR/diffstat.txt"
  git -C "$ROOT" status --porcelain > "$HANDOFF_DIR/status.txt"
fi

python - <<'PY'
import os
from pathlib import Path
import yaml

wo_path = Path(os.environ["WO_PATH"])
wo = yaml.safe_load(wo_path.read_text())

handoff = Path(os.environ["HANDOFF_DIR"]) / "handoff.md"
lines = [
    f"# Handoff {wo.get('id')}",
    "",
    f"Epic: {wo.get('epic_id')}",
    f"DoD: {wo.get('dod_id')}",
    "",
    "Deliverables:",
]
for item in wo.get("deliverables", []) or []:
    lines.append(f"- {item}")

handoff.write_text("\n".join(lines) + "\n")
PY

# Copy logs into handoff if present
LOG_DIR="$ROOT/_ctx/logs/$WO_ID"
if [[ -d "$LOG_DIR" ]]; then
  cp -R "$LOG_DIR"/* "$HANDOFF_DIR"/ 2>/dev/null || true
fi
