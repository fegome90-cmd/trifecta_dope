SKIP
fi
echo ""

# ============================================================================
# G4: Telemetry (opcional, FAIL-CLOSED si existe)
# ============================================================================
echo "=== G4: Telemetry Format Check ==="
if [ -f "_ctx/telemetry/events.jsonl" ]; then
    echo "Found events.jsonl, validating schema..."

    # AP1: jq parse
    if command -v jq &> /dev/null; then
        head -1 _ctx/telemetry/events.jsonl | \
            jq -c 'has("run_id"), has("segment_id"), has("timing_ms")' 2>&1 | \
            tee "${ARTIFACTS}/g4_telemetry_schema.txt"
        G4_PIPESTATUS=(${PIPESTATUS[*]})
        G4_SCHEMA_RC=${G4_PIPESTATUS[0]}

        if [ $G4_SCHEMA_RC -eq 0 ]; then
            GATE_RC[G4]=0  # PASS
            echo "Result: PASS"
        else
            GATE_RC[G4]=1  # FAIL
            echo "Result: FAIL (schema invalid, RC=$G4_SCHEMA_RC)"
        fi

        head -5 _ctx/telemetry/events.jsonl > "${ARTIFACTS}/g4_telemetry_sample.txt"
        echo "Sample events:"
        cat "${ARTIFACTS}/g4_telemetry_sample.txt"
    else
        echo "WARNING: jq not found, skipping validation"
        GATE_RC[G4]=255  # SKIP
    fi
else
    GATE_RC[G4]=255  # SKIP
    echo "Result: SKIP (no telemetry file)"
fi
echo ""

# ============================================================================
# SUMMARY: Gate Results con RCs ex
