#!/usr/bin/env bash
# Pre-commit hook: Acceptance Test Gate
# Ejecuta acceptance tests (not slow) si hay cambios en src/ o tests/

set -e

echo "🧪 Pre-commit: Acceptance Test Gate"
echo "   Running acceptance tests (not slow)..."

# Run acceptance tests with timeout
export TRIFECTA_TELEMETRY=off

if timeout 30s uv run pytest -q tests/acceptance -m "not slow" 2>&1; then
    echo "   ✅ Test gate passed"
    exit 0
else
    echo ""
    echo "   ❌ Test gate FAILED"
    echo "   Fix tests before committing or use: git commit --no-verify"
    exit 1
fi
