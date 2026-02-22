#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

log() { printf "%s\n" "$*"; }
fail() { printf "FAIL: %s\n" "$*" >&2; exit 1; }

# List staged files (one per line)
staged_files() {
  git diff --cached --name-only -z | tr '\0' '\n'
}

# Validate that a staged WO file in done/failed only changes allowed metadata keys.
# Commit message format is validated separately in the commit-msg hook.
validate_wo_metadata_update() {
  local file="$1"

  # 1. Path check
  if [[ ! "$file" =~ ^_ctx/jobs/(done|failed)/WO-.*\.ya?ml$ ]]; then
    return 1
  fi

  # 2. Stage-aware status check: block new files (A) and renames (R*) in done/failed
  #    Use --cached so we inspect staging, not working tree.
  local ns
  ns=$(git diff --cached --name-status -- "$file" | head -n1 | awk '{print $1}' || true)
  if [[ "$ns" == "A" || "$ns" == R* ]]; then
    log "[hooks] BLOCKED: new/renamed WO in done/failed: $file (use ctx_wo_finish.py)" >&2
    return 1
  fi

  # 3. Diff check: only allowed root-level keys.
  #    NOTE: This is intentionally simple (not a full YAML parser). It guards
  #    against obvious structural changes but defer deep invariants to CI / schema_validation.
  local allowed_keys="closed_at|closed_by|verified_at|verified_at_sha|evidence|result|x_governance_notes"

  local diff_lines
  diff_lines=$(git diff --cached --unified=0 "$file" \
    | grep -vE "^(---|\+\+\+|@@)" \
    | grep -E "^[+-]" \
    | sed 's/^[+-]//' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    || true)

  if [[ -z "$diff_lines" ]]; then
    return 0
  fi

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # Only check lines that look like top-level YAML keys (no indent, has colon)
    if [[ "$line" =~ ^[a-z_].*: ]]; then
      local key
      key=$(printf '%s' "$line" | cut -d: -f1)
      if [[ ! "$key" =~ ^($allowed_keys)$ ]]; then
        log "[hooks] BLOCKED: disallowed key '$key' modified in $file" >&2
        return 1
      fi

      # Evidence portability check: block absolute paths (not filesystem existence check)
      if [[ "$key" == "evidence" ]]; then
        local val
        val=$(printf '%s' "$line" | cut -d: -f2- | sed 's/^[[:space:]]*//')
        if [[ "$val" == /* ]]; then
          log "[hooks] BLOCKED: absolute evidence path is not portable: $val" >&2
          return 1
        fi
      fi
    fi
    # List items (- value) under evidence are passed through; deep validation belongs in CI.
  done <<< "$diff_lines"

  return 0
}

# ---------------------------------------------------------------------------
# Bypass helpers
# ---------------------------------------------------------------------------

_log_bypass() {
  local bypass_type="$1" reason="$2" bypass_key="$3"
  local script="$REPO_ROOT/scripts/hooks/log_bypass_telemetry.py"
  if [[ -f "$script" ]]; then
    python3 "$script" "$bypass_type" "$reason" --bypass-key "$bypass_key" >/dev/null 2>&1 || true
  fi
}

# Check bypass from the pending commit message FILE (for use in commit-msg hook).
check_pending_commit_msg_bypass() {
  local msg_file="${1:-}"
  local msg=""
  if [[ -n "$msg_file" && -f "$msg_file" ]]; then
    msg=$(head -n 1 "$msg_file" 2>/dev/null || echo "")
  fi
  if [[ "$msg" == *"[emergency]"* ]] || [[ "$msg" == *"[bypass]"* ]]; then
    _log_bypass "pending_commit_msg" "$msg" "commit_message_marker"
    return 0
  fi
  return 1
}

check_file_bypass() {
  local marker="$REPO_ROOT/.trifecta_hooks_bypass"
  if [[ -f "$marker" ]]; then
    local reason
    reason=$(head -n 1 "$marker" 2>/dev/null || echo "file bypass marker present")
    _log_bypass "file" "$reason" ".trifecta_hooks_bypass"
    return 0
  fi
  return 1
}

# should_bypass: accepts optional msg_file for commit-msg hook context.
# In pre-commit: call with no args (env var + file marker only — no git log).
# In commit-msg: call with the msg file path to also check message markers.
should_bypass() {
  local msg_file="${1:-}"
  if [[ "${TRIFECTA_HOOKS_DISABLE:-0}" == "1" ]]; then
    _log_bypass "env_var" "${TRIFECTA_WO_BYPASS_REASON:-unknown}" "TRIFECTA_HOOKS_DISABLE"
    return 0
  fi
  check_file_bypass && return 0
  if [[ -n "$msg_file" ]]; then
    check_pending_commit_msg_bypass "$msg_file" && return 0
  fi
  return 1
}
