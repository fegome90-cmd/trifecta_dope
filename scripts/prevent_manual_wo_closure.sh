#!/usr/bin/env bash
# Pre-commit guard: disallow manual WO closures.
# Expected closure transition per WO:
#   D _ctx/jobs/running/WO-XXXX.yaml
#   A _ctx/jobs/done|failed/WO-XXXX.yaml
# plus closed metadata (status, verified_at_sha, closed_at) in destination file.

set -euo pipefail

CHANGED_STATUS="$(git diff --cached --name-status)"

declare -a CLOSED_WO_FILES=()
while IFS=$'\t' read -r status path _rest; do
    [[ -z "${status:-}" || -z "${path:-}" ]] && continue
    if [[ "$path" =~ ^_ctx/jobs/(done|failed)/WO-.*\.yaml$ ]]; then
        CLOSED_WO_FILES+=("${status}:${path}")
    fi
done <<< "$CHANGED_STATUS"

[[ ${#CLOSED_WO_FILES[@]} -eq 0 ]] && exit 0

for item in "${CLOSED_WO_FILES[@]}"; do
    status="${item%%:*}"
    path="${item#*:}"

    if [[ "$status" != "A" && "$status" != R* ]]; then
        echo "TRIFECTA_ERROR_CODE: MANUAL_WO_CLOSURE_BLOCKED"
        echo "ERROR: Manual edit detected in ${path} (status ${status})."
        echo "Only closure transitions are allowed."
        exit 1
    fi

    wo_file="$(basename "$path")"
    wo_id="${wo_file%.yaml}"
    if ! echo "$CHANGED_STATUS" | grep -q "^D[[:space:]]_ctx/jobs/running/${wo_id}\.yaml$"; then
        echo "TRIFECTA_ERROR_CODE: MANUAL_WO_CLOSURE_BLOCKED"
        echo "ERROR: ${path} added without deleting _ctx/jobs/running/${wo_file}."
        echo "Use: uv run python scripts/ctx_wo_finish.py ${wo_id} --result done"
        exit 1
    fi

    if [[ ! -f "$path" ]]; then
        echo "TRIFECTA_ERROR_CODE: MANUAL_WO_CLOSURE_BLOCKED"
        echo "ERROR: staged file not found on disk: ${path}"
        exit 1
    fi

    target_state="$(echo "$path" | awk -F'/' '{print $3}')"
    if ! grep -q "^status:[[:space:]]*${target_state}[[:space:]]*$" "$path"; then
        echo "TRIFECTA_ERROR_CODE: MANUAL_WO_CLOSURE_BLOCKED"
        echo "ERROR: ${path} has invalid status. Expected status: ${target_state}."
        exit 1
    fi

    if ! grep -q "^verified_at_sha:" "$path" || ! grep -q "^closed_at:" "$path"; then
        echo "TRIFECTA_ERROR_CODE: MANUAL_WO_CLOSURE_BLOCKED"
        echo "ERROR: ${path} missing closure metadata (verified_at_sha/closed_at)."
        exit 1
    fi
done

exit 0
