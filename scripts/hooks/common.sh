#!/usr/bin/env bash
set -euo pipefail

log() { printf "%s\n" "$*"; }
fail() { printf "FAIL: %s\n" "$*" >&2; exit 1; }

# list staged files
staged_files() {
  git diff --cached --name-only -z | tr '\0' '\n'
}
