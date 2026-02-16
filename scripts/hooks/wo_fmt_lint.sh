#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

if ! staged_files | grep -qE '^_ctx/jobs/(pending|running|done|failed)/WO-.*\.ya?ml$'; then
  log "[hooks] no WO YAML changes, skipping fmt/lint"
  exit 0
fi

log "[hooks] WO YAML touched → fmt + lint"
uv run python scripts/ctx_wo_fmt.py
uv run python scripts/ctx_wo_lint.py --strict
log "[hooks] WO fmt/lint PASS"
