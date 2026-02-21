#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=scripts/hooks/common.sh
source "$REPO_ROOT/scripts/hooks/common.sh"

COMMIT_MSG_FILE="${1:-}"

if should_bypass "$COMMIT_MSG_FILE"; then
  log "[hooks] bypassing prevent_manual_wo_closure (emergency/bypass detected)"
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
    fail "Cannot close WO while mutating closure scripts in same commit. Split into two commits."
fi

for item in "${CLOSED_WO_FILES[@]}"; do
    status="${item%%:*}"
    path="${item#*:}"

    if [[ "$status" != "A" && "$status" != R* ]]; then
        fail "Manual edit detected in ${path} (status ${status}). Only closure transitions allowed."
    fi

    wo_file="$(basename "$path")"
    wo_id="${wo_file%.yaml}"
    if ! echo "$CHANGED_STATUS" | grep -q "^D[[:space:]]_ctx/jobs/running/${wo_id}\.yaml$"; then
        fail "${path} added without deleting _ctx/jobs/running/${wo_file}. Use ctx_wo_finish.py"
    fi

    if [[ ! -f "$path" ]]; then
        fail "Staged file not found on disk: ${path}"
    fi

    target_state="$(echo "$path" | awk -F'/' '{print $3}')"
    if ! grep -q "^status:[[:space:]]*${target_state}[[:space:]]*$" "$path"; then
        fail "${path} has invalid status. Expected: ${target_state}"
    fi

    if ! grep -q "^verified_at_sha:" "$path" || ! grep -q "^closed_at:" "$path"; then
        fail "${path} missing closure metadata (verified_at_sha/closed_at)"
    fi

    if ! echo "$CHANGED_STATUS" | grep -qE "^[AMR].*[[:space:]]_ctx/handoff/${wo_id}/verdict\.json$"; then
        fail "Missing staged handoff verdict for ${wo_id}"
    fi

    if ! echo "$CHANGED_STATUS" | grep -qE "^[AMR].*[[:space:]]_ctx/handoff/${wo_id}/verification_report\.log$"; then
        fail "Missing staged verification report for ${wo_id}"
    fi
done

exit 0
