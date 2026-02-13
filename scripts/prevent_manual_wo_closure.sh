#!/usr/bin/env bash
# Pre-commit hook to prevent manual edits to _ctx/jobs/done/
# Only allows commits via ctx_wo_finish.py

set -euo pipefail

CHANGED_FILES=$(git diff --cached --name-only)
if echo "$CHANGED_FILES" | grep -q "^_ctx/jobs/done/"; then
    # Check if ctx_wo_finish.py is being updated in the same commit
    if ! git diff --cached --name-only | grep -q "scripts/ctx_wo_finish.py"; then
        echo "ERROR: Manual edits to _ctx/jobs/done/ are prohibited."
        echo "Use: python scripts/ctx_wo_finish.py WO-XXXX --result done"
        exit 1
    fi
fi
exit 0
