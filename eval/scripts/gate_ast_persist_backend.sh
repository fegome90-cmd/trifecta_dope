#!/usr/bin/env bash
# Gate: AST Persistence Backend Verification
# Purpose: Ensure persistence flag correctly switches between backends
# Exit 0 (PASS) if both backends work as expected
# Exit 1 (FAIL) if backend mismatch detected

set -euo pipefail

SEGMENT="${1:-.}"
TARGET_URI="sym://python/mod/src.domain.models"
TELEMETRY_FILE="_ctx/telemetry/events.jsonl"

echo "=== AST Persistence Backend Gate ==="
echo "Segment: $SEGMENT"
echo ""

# Gate 1: With TRIFECTA_AST_PERSIST=1 (or default if .envrc loaded)
echo "[Gate 1] Testing with TRIFECTA_AST_PERSIST=1..."
RUN_ID_ON="gate_on_$(date +%s)"
TRIFECTA_AST_PERSIST=1 TRIFECTA_RUN_ID="$RUN_ID_ON" uv run trifecta ast symbols "$TARGET_URI" --segment "$SEGMENT" --telemetry full > /dev/null 2>&1

BACKEND_ON=$(rg "\"run_id\": \"$RUN_ID_ON\"" "$TELEMETRY_FILE" | rg '"backend"' | head -1 | grep -o '"backend": "[^"]*"' | cut -d'"' -f4)
echo "  Backend: $BACKEND_ON"

if [[ "$BACKEND_ON" != "FileLockedAstCache" ]]; then
    echo "  ❌ FAIL: Expected FileLockedAstCache, got $BACKEND_ON"
    exit 1
fi
echo "  ✅ PASS"

# Gate 2: With TRIFECTA_AST_PERSIST=0 (explicit OFF)
echo "[Gate 2] Testing with TRIFECTA_AST_PERSIST=0..."
RUN_ID_OFF="gate_off_$(date +%s)"
TRIFECTA_AST_PERSIST=0 TRIFECTA_RUN_ID="$RUN_ID_OFF" uv run trifecta ast symbols "$TARGET_URI" --segment "$SEGMENT" --telemetry full > /dev/null 2>&1

BACKEND_OFF=$(rg "\"run_id\": \"$RUN_ID_OFF\"" "$TELEMETRY_FILE" | rg '"backend"' | head -1 | grep -o '"backend": "[^"]*"' | cut -d'"' -f4)
echo "  Backend: $BACKEND_OFF"

if [[ "$BACKEND_OFF" != "InMemoryLRUCache" ]]; then
    echo "  ❌ FAIL: Expected InMemoryLRUCache, got $BACKEND_OFF"
    exit 1
fi
echo "  ✅ PASS"

echo ""
echo "=== GATE PASSED ==="
echo "Persistence flag correctly switches backends."
exit 0
