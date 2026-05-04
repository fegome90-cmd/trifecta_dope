#!/bin/bash
# scripts/trifecta_manager.sh - Pure Trifecta Motor Lifecycle Manager
# Focused ONLY on Context, AST, Graph and LSP.

set -euo pipefail

REPO_ID="6f25e381"
# F1 Engine Fix: Use canonical short paths from /tmp to avoid AF_UNIX limits
PID_FILE="/tmp/trifecta_lsp_${REPO_ID}.pid"
LOCK_FILE="/tmp/trifecta_lsp_${REPO_ID}.lock"

TRIFECTA_BIN=$(command -v trifecta || echo "uv run trifecta")

_is_running() {
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if [[ "$pid" -gt 0 ]] && ps -p "$pid" > /dev/null 2>&1; then
        if ps -p "$pid" -o args= 2>/dev/null | grep -q "daemon"; then
            return 0
        fi
    fi
    return 1
}

status() {
    if _is_running; then
        echo "Motor Daemon: RUNNING (PID: $(cat $PID_FILE))"
        return 0
    else
        echo "Motor Daemon: STOPPED"
        return 1
    fi
}

start() {
    if _is_running; then return 0; fi
    # Clean stale locks
    rm -f "$PID_FILE" "$LOCK_FILE"
    $TRIFECTA_BIN daemon start --repo . > /dev/null 2>&1
}

stop() {
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if [[ "$pid" -gt 0 ]]; then kill "$pid" 2>/dev/null || true; fi
    rm -f "$PID_FILE" "$LOCK_FILE"
}

warmup() {
    echo "🏎️ Ignition: Building Context..."
    $TRIFECTA_BIN ctx sync --segment .
    echo "🧠 Intelligence: Indexing Graph..."
    $TRIFECTA_BIN graph index --segment .
    echo "🛰️ Runtime: Starting Daemon..."
    start
    echo "DONE: Motor fully operational."
}

case "${1:-status}" in
    start|stop|status|warmup) "$1" ;;
    *) echo "Usage: $0 {start|stop|status|warmup}"; exit 1 ;;
esac
