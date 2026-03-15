#!/usr/bin/env bash
set -euo pipefail

DIFF_RANGE="${1:-${BR_DIFF_RANGE:-main...HEAD}}"

BIOME_FILES=()
while IFS= read -r file; do
  [[ -n "$file" ]] && BIOME_FILES+=("$file")
done < <(
  git diff --name-only --diff-filter=ACMR "$DIFF_RANGE" \
    | grep -E '\.(ts|tsx|js|jsx|mjs|cjs|json|jsonc)$' || true
)

if [[ "${#BIOME_FILES[@]}" -eq 0 ]]; then
  echo "No files were processed"
  exit 0
fi

bunx @biomejs/biome check --files-ignore-unknown=true "${BIOME_FILES[@]}"
