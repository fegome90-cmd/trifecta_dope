#!/usr/bin/env bash
# Gate: Clean Worktree Reproducibility
# Validates that repro test passes in clean worktree without pre-existing state

set -euo pipefail

echo "=== Clean Worktree Reproducibility Gate ==="

# Capture HEAD SHA
HEAD=$(git rev-parse HEAD)
echo "HEAD: $HEAD"

# Create clean worktree
WT="/tmp/tf_repro_gate_${HEAD:0:8}"
echo "Creating worktree at: $WT"

# Cleanup function
cleanup() {
    cd - >/dev/null 2>&1 || true
    if [ -d "$WT" ]; then
        echo "Cleaning up worktree..."
        git worktree remove "$WT" --force 2>/dev/null || rm -rf "$WT"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Remove if exists
if [ -d "$WT" ]; then
    echo "Removing existing worktree..."
    git worktree remove "$WT" --force 2>/dev/null || rm -rf "$WT"
fi

# Add worktree
git worktree add "$WT" "$HEAD"

# Enter worktree
cd "$WT"

# Remove any _ctx state
echo "Removing pre-existing _ctx state..."
rm -rf _ctx || true

# Install dependencies
echo "Installing dependencies..."
uv sync --all-groups
uv pip install pytest pytest-cov  # Ensure test deps available

# Verify Python
echo "Python version:"
uv run python -V

# Run repro test
echo "Running reproducibility test..."
uv run pytest -xvs tests/integration/test_repro_clean_sync_then_search.py

# Capture exit code
TEST_EXIT=$?

# Report result
if [ $TEST_EXIT -eq 0 ]; then
    echo "✅ GATE PASS: Clean boot reproducibility validated"
    exit 0
else
    echo "❌ GATE FAIL: Reproducibility test failed in clean worktree"
    exit 1
fi
