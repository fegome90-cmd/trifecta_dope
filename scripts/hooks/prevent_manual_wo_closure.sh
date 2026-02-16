#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

if [[ "${TRIFECTA_ALLOW_MANUAL_WO_CLOSURE:-0}" == "1" ]]; then
  log "[hooks] manual WO closure override enabled"
  exit 0
fi

if staged_files | grep -qE '^_ctx/jobs/(done|failed)/WO-.*\.ya?ml$' ; then
  fail "Manual edits to _ctx/jobs/(done|failed) forbidden. Use ctx_wo_finish.py. Override: TRIFECTA_ALLOW_MANUAL_WO_CLOSURE=1"
fi
