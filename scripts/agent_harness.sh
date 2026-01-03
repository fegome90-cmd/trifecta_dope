#!/usr/bin/env bash
set -euo pipefail

# Trifecta Smoke Test - Simple Version
# Usage: ./agent_harness.sh [segment_path]

SEGMENT="${1:-.}"
echo "🔍 Running Trifecta smoke tests on segment: $SEGMENT"
echo

# 0) Info mínima (evita "funciona en mi máquina")
echo "▶️  Environment Info"
python --version
uv --version || echo "⚠️  uv not found, but continuing..."
echo

# 1) Baseline: help debe funcionar
echo "▶️  Help Check"
uv run trifecta --help > /dev/null || { echo "❌ FAIL: trifecta --help failed"; exit 1; }
echo "✅ Help check passed"
echo

# 2) CTX sync en el segmento actual
echo "▶️  CTX Sync"
uv run trifecta ctx sync -s "$SEGMENT" 2>&1 | tee /tmp/tf_sync.log
SYNC_RESULT=${PIPESTATUS[0]}
if [ $SYNC_RESULT -eq 0 ]; then
    echo "✅ CTX sync passed"
else
    echo "❌ FAIL: CTX sync failed with code $SYNC_RESULT"
    exit 1
fi
echo

# 3) CTX search (busca algo que seguro exista)
echo "▶️  CTX Search"
uv run trifecta ctx search -s "$SEGMENT" -q "telemetry" 2>&1 | tee /tmp/tf_search.log
SEARCH_RESULT=${PIPESTATUS[0]}
if [ $SEARCH_RESULT -eq 0 ]; then
    echo "✅ CTX search passed"
else
    echo "❌ FAIL: CTX search failed with code $SEARCH_RESULT"
    exit 1
fi
echo

echo "========================================="
echo "✅ ALL SMOKE TESTS PASSED"
echo "Logs: /tmp/tf_*.log"
echo "========================================="
