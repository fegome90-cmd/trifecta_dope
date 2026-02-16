#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

# Get commit message (first line only)
COMMIT_MSG=$(git log -1 --format=%s 2>/dev/null || echo "")

# Check for emergency bypass in commit message (not env var)
if [[ "$COMMIT_MSG" == *"[emergency]"* ]] || [[ "$COMMIT_MSG" == *"[bypass]"* ]]; then
  log "[hooks] emergency/bypass detected in commit message, allowing WO closure"
  exit 0
fi

if staged_files | grep -qE '^_ctx/jobs/(done|failed)/WO-.*\.ya?ml$' ; then
  fail "Manual edits to _ctx/jobs/(done|failed) forbidden. Use ctx_wo_finish.py. Emergency bypass: git commit -m 'fix: [emergency] reason'"
fi
