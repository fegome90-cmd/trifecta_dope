#!/usr/bin/env bash
# wo_exit.sh - Unified entrypoint to finish a Work Order
# Usage: bash scripts/wo_exit.sh <WO_ID> [--root PATH] [--result done|failed]

set -euo pipefail

WO_ID="${1:-}"
ROOT="."
RESULT="done"

if [[ -z "$WO_ID" ]]; then
  echo "Usage: scripts/wo_exit.sh <WO_ID> [--root PATH] [--result done|failed]"
  exit 2
fi

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --result)
      RESULT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

echo "🚀 Exiting Work Order: $WO_ID"
uv run python scripts/ctx_wo_finish.py "$WO_ID" --root "$ROOT" --result "$RESULT"
