#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

# Check all bypass mechanisms (env var, commit message, file marker)
# Uses should_bypass() from common.sh which logs telemetry
if should_bypass; then
  exit 0
fi

if staged_files | grep -qE '^_ctx/jobs/(done|failed)/WO-.*\.ya?ml$' ; then
  fail "Manual edits to _ctx/jobs/(done|failed) forbidden. Use ctx_wo_finish.py. Emergency bypass: git commit -m 'fix: [emergency] reason'"
fi
