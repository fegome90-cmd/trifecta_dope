#!/bin/bash
# Pre-commit hook wrapper for ctx sync
# Runs ctx sync and always returns success to allow commit

set -e

echo "🔄 Running ctx sync..."
uv run trifecta ctx sync -s . > /dev/null 2>&1 || echo "⚠️  ctx sync had issues, but continuing..."

exit 0
