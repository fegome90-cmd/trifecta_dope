#!/usr/bin/env bash
# Verify pre-commit does not leave dirty worktree (Auditable Logic)
set -e

echo "⚙️🧨 Running Auditable Pre-commit Tripwire..."
PRECOMMIT_OUTPUT=$(uv run pre-commit run --all-files 2>&1 || true)
echo "$PRECOMMIT_OUTPUT"

# BLOCK 1: Check for pre-commit "files were modified" string
if echo "$PRECOMMIT_OUTPUT" | grep -q "files were modified by this hook"; then
    echo "❌ TRIPWIRE FAILED: Pre-commit detected side-effects ('files were modified by this hook')."
    exit 1
fi

# BLOCK 2: Check for dirty worktree (excluding allowed paths)
# Only check non-telemetry files for modifications
DIRTY_FILES=$(git status --porcelain | grep -v "_ctx/telemetry/" | grep -v "hookify_violations.jsonl" || true)
if [ -n "$DIRTY_FILES" ]; then
    echo "❌ TRIPWIRE FAILED: Pre-commit hooks modified the working tree or left untracked files."
    echo "$DIRTY_FILES"
    exit 1
fi

echo "✅ TRIPWIRE PASSED: Worktree is clean and no side-effects detected."
exit 0
