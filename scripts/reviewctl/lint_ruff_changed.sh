#!/usr/bin/env bash
set -euo pipefail

DIFF_RANGE="${1:-${BR_DIFF_RANGE:-main...HEAD}}"

PYTHON_FILES=()
while IFS= read -r file; do
  [[ -n "$file" ]] && PYTHON_FILES+=("$file")
done < <(
  git diff --name-only --diff-filter=ACMR "$DIFF_RANGE" \
    | grep -E '\.pyi?$' || true
)

if [[ "${#PYTHON_FILES[@]}" -eq 0 ]]; then
  echo "warning: No Python files found"
  exit 0
fi

uv run ruff check "${PYTHON_FILES[@]}"
