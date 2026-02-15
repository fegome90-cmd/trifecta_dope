#!/bin/bash
# install-hooks.sh - Install git hooks for documentation automation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR"

echo "📦 Installing Trifecta documentation hooks..."

# Check if already configured
EXISTING_HOOKS_PATH=$(git config --get core.hooksPath 2>/dev/null || true)

if [[ -n "$EXISTING_HOOKS_PATH" ]]; then
    echo ""
    echo "⚠️  WARNING: hooksPath already configured!"
    echo "    Current: $EXISTING_HOOKS_PATH"
    echo "    New:     scripts/hooks"
    echo ""
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. To configure manually:"
        echo "   git config core.hooksPath scripts/hooks"
        exit 1
    fi
fi

# Set hooks path
git config core.hooksPath "$HOOKS_DIR"
echo "✅ Set core.hooksPath to: $HOOKS_DIR"

# Ensure pre-commit is executable
chmod +x "$HOOKS_DIR/pre-commit"
echo "✅ Made pre-commit executable"

# Check for uv
if command -v uv &>/dev/null; then
    echo "✅ uv found - ctx sync will work"
else
    echo "⚠️  uv not found - install uv for ctx sync support"
    echo "   See: https://github.com/astral-sh/uv"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Hooks installed successfully!"
echo ""
echo "What this does:"
echo "  - Validates docs on every commit"
echo "  - Runs verify_documentation.sh"
echo "  - Syncs context pack (if uv available)"
echo ""
echo "To bypass: git commit --no-verify"
echo "To disable: TRIFECTA_HOOKS_DISABLE=1 git commit ..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
