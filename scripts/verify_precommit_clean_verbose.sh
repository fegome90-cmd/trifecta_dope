#!/usr/bin/env bash
# Tripwire: Verifies that pre-commit run --all-files does not leave dirty artifacts.

set -e

echo "⚙️🧨 Running Auditable Pre-commit Tripwire..."
uv run pre-commit run --all-files --verbose

if [ -n "$(git status --porcelain)" ]; then
    echo "❌ TRIPWIRE FAILED: Pre-commit hooks modified the working tree or left untracked files."
    git status --porcelain
    exit 1
fi

echo "✅ TRIPWIRE PASSED: Clean execution verified."
exit 0
