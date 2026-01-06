#!/bin/bash
set -e

# Defaults
OPS=${OPS:-10}
WORKERS=${WORKERS:-2}
RUN_ID=${RUN_ID:-"soak_$(date +%s)"}
TARGET_SEGMENT=${SEGMENT:-"."}

# Export for telemetry correlation
export TRIFECTA_RUN_ID="$RUN_ID"

# Paths
LOG_DIR="_ctx/logs/wo_p3_0"
mkdir -p "$LOG_DIR"
RUN_LOG="$LOG_DIR/${RUN_ID}_main.log"

# Target Module for heavy AST work (using a large file in the repo)
# finding a large python file to parse repeatedly
TARGET_FILE="src/infrastructure/lsp_daemon.py"
TARGET_URI="sym://python/mod/src.infrastructure.lsp_daemon"

echo "=== AST Soak Run $RUN_ID ===" > "$RUN_LOG"
echo "Config: OPS=$OPS, WORKERS=$WORKERS, SEGMENT=$TARGET_SEGMENT" >> "$RUN_LOG"

# 1. Clean DB (Deterministic Path for Segment '.')
# Based on T1 evidence: .trifecta/cache/ast_cache_*.db
echo "[Setup] Cleaning cache..." >> "$RUN_LOG"
# Note: In a real soak we might want to keep it, but for T2 gate we clean.
# We'll use the CLI to clear cache to be safe/portable if possible, 
# or just rm the file if we know the path. 
# Better: use TRIFECTA_AST_PERSIST=1 and rm the specific db file for the segment.
# Assuming cwd is the segment root.
rm -f .trifecta/cache/ast_cache_*.db >> "$RUN_LOG" 2>&1

# 2. Worker Function
run_worker() {
    local worker_id=$1
    local count=$2
    local log_file="$LOG_DIR/${RUN_ID}_worker_${worker_id}.log"
    
    echo "Worker $worker_id starting $count ops..." > "$log_file"
    
    for ((i=1; i<=count; i++)); do
        # Use valid CLI command to extract symbols (reads/writes cache)
        # Using persist flag explicitly to ensure it hits the DB logic
        # We assume the env var is set globally, but adding flag is safer if supported.
        # Checking skill.md: trifecta ast symbols "sym..." --persist-cache
        
        uv run trifecta ast symbols "$TARGET_URI" --segment "$TARGET_SEGMENT" --telemetry full --persist-cache >> "$log_file" 2>&1
        local rc=$?
        
        if [ $rc -ne 0 ]; then
            echo "Error in op $i (RC=$rc)" >> "$log_file"
            # Fail closed? Or count errors? For soak, we log errors.
        fi
    done
    echo "Worker $worker_id finished." >> "$log_file"
}

# 3. Execution
echo "[Run] Starting $WORKERS workers with $((OPS / WORKERS)) ops each..." >> "$RUN_LOG"
pids=""

ops_per_worker=$((OPS / WORKERS))

for ((w=1; w<=WORKERS; w++)); do
    run_worker "$w" "$ops_per_worker" &
    pids="$pids $!"
done

# 4. Wait
for pid in $pids; do
    wait "$pid"
done

echo "[Done] All workers finished." >> "$RUN_LOG"

# 5. Validation (Simple check of log size/presence)
lines=$(cat "$LOG_DIR"/${RUN_ID}_worker_*.log | wc -l)
echo "Total log lines: $lines" >> "$RUN_LOG"

# Output summary to stdout
cat "$RUN_LOG"

# Exit 0
exit 0
