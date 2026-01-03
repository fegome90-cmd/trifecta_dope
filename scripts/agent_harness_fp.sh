#!/usr/bin/env bash
set -uo pipefail

# Trifecta Smoke Test - Functional/Compositional Version
# Usage: ./agent_harness_fp.sh [segment_path] [tmp_dir] [stop_on_fail]
# Example: ./agent_harness_fp.sh . /tmp 0  # Run all tests even if some fail

# =========================
# "Result" / data helpers
# =========================
mk_result() {
  local name="$1" code="$2" log="$3"
  printf "%s\t%s\t%s\n" "$name" "$code" "$log"
}

# =========================
# Impure edge: executor
# =========================
run_step() {
  local name="$1"; shift
  local log_path="$1"; shift
  local -a cmd=( "$@" )

  echo "▶️  $name"
  echo "    cmd: ${cmd[*]}"
  if "${cmd[@]}" 2>&1 | tee "$log_path"; then
    return 0
  else
    local code="${PIPESTATUS[0]}"
    return "$code"
  fi
}

# =========================
# Pure-ish core: plan builder
# =========================
build_plan() {
  local segment="${1:-.}"
  local tmp="${2:-/tmp}"
  # Delimitador: | (más seguro que tab)
  cat <<-'EOF'
	info_minima|1|/tmp/tf_info.log|python --version
	uv_version|0|/tmp/tf_uv_version.log|uv --version
	help|1|/tmp/tf_help.log|uv run trifecta --help
	ctx_sync|1|/tmp/tf_sync.log|uv run trifecta ctx sync -s SEGMENT
	ctx_search_telemetry|1|/tmp/tf_search.log|uv run trifecta ctx search -s SEGMENT -q telemetry
	EOF
  # Replace SEGMENT placeholder
  sed "s|SEGMENT|$segment|g"
}

# =========================
# Fold runner
# =========================
run_plan() {
  local segment="${1:-.}"
  local tmp="${2:-/tmp}"
  local stop_on_fail="${3:-1}"

  local any_fail=0
  local -a results=()

  while IFS='|' read -r name required log_path cmdline; do
    [[ -z "$name" ]] && continue

    local -a cmd
    eval "cmd=($cmdline)"

    if run_step "$name" "$log_path" "${cmd[@]}"; then
      results+=( "$(mk_result "$name" 0 "$log_path")" )
    else
      local code=$?
      results+=( "$(mk_result "$name" "$code" "$log_path")" )
      if [[ "$required" == "1" ]]; then
        any_fail=1
        if [[ "$stop_on_fail" == "1" ]]; then
          echo "❌ Critical step '$name' failed with code $code. Stopping."
          break
        fi
      fi
    fi
    echo
  done < <(build_plan "$segment" "$tmp")

  echo "========================================="
  echo "SUMMARY (TSV)"
  echo "========================================="
  echo -e "name\tcode\tlog"
  printf "%s\n" "${results[@]}"
  echo

  if [[ $any_fail -eq 0 ]]; then
    echo "✅ ALL TESTS PASSED"
  else
    echo "❌ SOME TESTS FAILED"
  fi

  return "$any_fail"
}

# =========================
# Main
# =========================
main() {
  local segment="${1:-.}"
  local tmp="${2:-/tmp}"
  local stop_on_fail="${3:-0}"

  echo "🔍 Trifecta Functional Harness"
  echo "Segment: $segment"
  echo "Stop on fail: $stop_on_fail"
  echo

  run_plan "$segment" "$tmp" "$stop_on_fail"
}

main "$@"
