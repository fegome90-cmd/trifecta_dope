#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=scripts/hooks/common.sh
source "$REPO_ROOT/scripts/hooks/common.sh"

if should_bypass ""; then
  log "[hooks] bypassing prevent_manual_wo_closure (env var detected)"
  exit 0
fi

CHANGED_STATUS="$(git diff --cached --name-status)"

declare -a CLOSED_WO_FILES=()
while IFS=$'\t' read -r status path _rest; do
    [[ -z "${status:-}" || -z "${path:-}" ]] && continue
    if [[ "$path" =~ ^_ctx/jobs/(done|failed)/WO-.*\.yaml$ ]]; then
        CLOSED_WO_FILES+=("${status}:${path}")
    fi
done <<< "$CHANGED_STATUS"

[[ ${#CLOSED_WO_FILES[@]} -eq 0 ]] && exit 0

if echo "$CHANGED_STATUS" | grep -qE "^[AMR].*[[:space:]]scripts/(ctx_wo_finish\.py|prevent_manual_wo_closure\.sh)$"; then
    fail "Cannot close WO while mutating closure scripts. Split into two commits."
fi

fail "Manual edits to _ctx/jobs/(done|failed) forbidden. Use ctx_wo_finish.py.
Emergency bypass: TRIFECTA_WO_BYPASS_REASON='reason' git commit -m '...'
Note: [emergency] tag in message is for audit only, does NOT bypass pre-commit."
