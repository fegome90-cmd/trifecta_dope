]=1  # FAIL
    echo "Result: FAIL (FILE_NOT_FOUND)"
else
    GATE_RC[G3]=0  # PASS (error diferente es aceptable)
    echo "Result: PASS (error is not FILE_NOT_FOUND)"
fi
echo ""

# ============================================================================
# G4: Telemetry (opcional, FAIL-CLOSED si existe)
# ============================================================================
echo "=== G4: Telemetry Format Check ==="
if [ -f "_ctx/telemetry/events.jsonl" ]; then
    echo "Found events.jsonl, validating schema..."
    head -1 _ctx/telemetry/events.jsonl | jq -c 'has("run_id"), has("segment_id"), has("timing_ms")' > "${ARTIFACTS}/telemetry_schema.txt" 2>&1
    G4_SCHEMA_RC=$?

    if [ $G4_SCHEMA_RC -eq 0 ]; then
        GATE_RC[G4]=0  # PASS
        echo "Result: PASS"
    else
        GATE_RC[G4]=1  # FAIL
        echo "Result: FAIL (schema invalid)"
    fi

    head -5 _ctx/telemetry/events.jsonl > "${ARTIFACTS}/telemetry_sample.txt"
    echo "Sample events:"
    cat "${ARTIFACTS}/telemetry_sample.txt"
else
    GATE_RC[G4]=255  # SKIP
    echo "Result: SKIP (no telemetry file)"
fi
echo ""

# ============================================================================
# SUMMARY: Gate Results con RCs explícitos
# ============================================================================
echo ""
echo "=== FINAL GATE RESULTS ==="
echo "G1 (pytest collecting): RC=${GATE
