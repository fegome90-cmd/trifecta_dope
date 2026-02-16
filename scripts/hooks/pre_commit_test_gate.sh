#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

CMD="${TRIFECTA_PRECOMMIT_TEST_CMD:-}"

if [[ -z "$CMD" ]]; then
  log "[hooks] test gate disabled (TRIFECTA_PRECOMMIT_TEST_CMD not set)"
  exit 0
fi

if ! staged_files | grep -qE '^(scripts/|src/|tests/|pyproject\.toml|uv\.lock)$'; then
  log "[hooks] test gate skipped (no relevant staged changes)"
  exit 0
fi

log "[hooks] test gate running: $CMD"
$CMD
log "[hooks] test gate PASS"
