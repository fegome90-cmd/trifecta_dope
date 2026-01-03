#!/usr/bin/env bash
# Pre-commit hook: Acceptance Test Gate
# Ejecuta acceptance tests (not slow) si hay cambios en src/ o tests/

set -e

echo "🧪 Pre-commit: Acceptance Test Gate"
echo "   Running acceptance tests (not slow)..."

# Run acceptance tests with timeout
# CRITICAL: Redirect telemetry to /tmp to keep repo clean during pre-commit
# Tests can still validate telemetry behavior, but writes go to temp directory
export TRIFECTA_TELEMETRY_DIR="/tmp/trifecta_test_telemetry_$$"
mkdir -p "$TRIFECTA_TELEMETRY_DIR"

# HARDENING: Cleanup best-effort on exit
trap "rm -rf $TRIFECTA_TELEMETRY_DIR" EXIT

# INVARIANT CHECK: Ensure redirection is active
if [ -z "$TRIFECTA_TELEMETRY_DIR" ]; then
    echo "   ❌ FATAL: TRIFECTA_TELEMETRY_DIR is not set. Aborting to prevent repo contamination."
    exit 1
fi

if timeout 30s uv run pytest -q tests/acceptance -m "not slow" 2>&1; then
    echo "   ✅ Test gate passed"
    exit 0
else
    echo ""
    echo "   ❌ Test gate FAILED"
    echo "   Fix tests before committing or use: git commit --no-verify"
    exit 1
fi
