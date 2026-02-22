#!/usr/bin/env bash
# wo_fmt_lint.sh: Run WO formatter and linter on STAGED WO YAML files only.
#
# Policy:
#   - Staged deletions only → skip (nothing to format)
#   - Staged add/modify     → fmt + lint on THOSE files only
#   - Global lint (_ctx/jobs/**) belongs in CI / make gate-all, NOT here
set -euo pipefail
source "$(dirname "$0")/common.sh"

# Collect staged WO YAML paths (all states)
staged_wo=$(git diff --cached --name-only -z \
  | tr '\0' '\n' \
  | grep -E '^_ctx/jobs/(pending|running|done|failed)/WO-.*\.ya?ml$' \
  || true)

if [[ -z "$staged_wo" ]]; then
  log "[hooks] no WO YAML changes, skipping fmt/lint"
  exit 0
fi

# Determine staged WO files that are NOT deleted (A=Added, M=Modified, R=Renamed, C=Copied)
staged_wo_nondel=$(git diff --cached --name-status \
  | awk '$1 !~ /^D/ {print $2}' \
  | grep -E '^_ctx/jobs/(pending|running|done|failed)/WO-.*\.ya?ml$' \
  || true)

if [[ -z "$staged_wo_nondel" ]]; then
  log "[hooks] WO YAML: staged changes are deletions only, skipping fmt/lint"
  exit 0
fi

log "[hooks] WO YAML touched (non-delete) → fmt + lint on staged files only"

# Build --files arguments for ctx_wo_fmt.py
files_args=()
while IFS= read -r wo_file; do
  [[ -z "$wo_file" || ! -f "$wo_file" ]] && continue
  files_args+=("$wo_file")
done <<< "$staged_wo_nondel"

if [[ ${#files_args[@]} -eq 0 ]]; then
  log "[hooks] no valid staged WO files to process"
  exit 0
fi

# Format staged files only (--files bypasses global _iter_wo_files scan)
uv run python scripts/ctx_wo_fmt.py --write --files "${files_args[@]}" \
  || fail "WO fmt failed"

# Re-stage any formatting changes
for f in "${files_args[@]}"; do
  git add "$f" 2>/dev/null || true
done

# Lint staged files using --wo-id if supported; otherwise skip and defer to CI
for wo_file in "${files_args[@]}"; do
  wo_id=$(basename "$wo_file" .yaml)
  if uv run python scripts/ctx_wo_lint.py --strict --wo-id "$wo_id" 2>/dev/null; then
    : # pass
  elif uv run python scripts/ctx_wo_lint.py --help 2>&1 | grep -q -- "--wo-id"; then
    fail "WO lint failed for $wo_id"
  else
    log "[hooks] WARNING: ctx_wo_lint.py has no --wo-id; global lint deferred to CI"
    break
  fi
done

log "[hooks] WO fmt/lint PASS"
