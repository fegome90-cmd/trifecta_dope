#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

log() { printf "%s\n" "$*"; }
fail() { printf "FAIL: %s\n" "$*" >&2; exit 1; }

# List staged files (one per line)
staged_files() {
  git diff --cached --name-only -z | tr '\0' '\n'
}

_log_bypass() {
  local bypass_type="$1"
  local reason="$2"
  local bypass_key="$3"

  local script="$REPO_ROOT/scripts/hooks/log_bypass_telemetry.py"
  if [[ -f "$script" ]]; then
    if ! python3 "$script" "$bypass_type" "$reason" --bypass-key "$bypass_key" >/dev/null 2>&1; then
      log "[hooks] WARNING: telemetry logging failed for bypass: $bypass_type - $reason" >&2
    fi
  fi
}

check_commit_msg_bypass() {
  local msg
  msg=$(git log -1 --format=%s 2>/dev/null || echo "")
  if [[ "$msg" == *"[emergency]"* ]] || [[ "$msg" == *"[bypass]"* ]]; then
    _log_bypass "commit_msg" "$msg" "commit_message_marker"
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

should_bypass() {
  if [[ "${TRIFECTA_HOOKS_DISABLE:-0}" == "1" ]]; then
    local reason="${TRIFECTA_WO_BYPASS_REASON:-}"
    if [[ -z "$reason" ]]; then
      fail "TRIFECTA_HOOKS_DISABLE=1 requires TRIFECTA_WO_BYPASS_REASON"
    fi
    _log_bypass "env_var" "$reason" "TRIFECTA_WO_BYPASS_REASON"
    return 0
  fi

  if check_commit_msg_bypass; then
    return 0
  fi

  if check_file_bypass; then
    return 0
  fi

  return 1
}
