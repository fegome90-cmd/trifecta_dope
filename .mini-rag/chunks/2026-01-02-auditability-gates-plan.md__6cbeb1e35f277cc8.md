o "=== FINAL GATE RESULTS ==="
echo "G1 (pytest collecting): RC=${GATE_RC[G1]} ($([ ${GATE_RC[G1]} -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G2 (path hygiene):      RC=${GATE_RC[G2]} ($([ ${GATE_RC[G2]} -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G3 (ast symbols):       RC=${GATE_RC[G3]} ($([ ${GATE_RC[G3]} -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G4 (telemetry):         RC=${GATE_RC[G4]} ($([ ${GATE_RC[G4]} -eq 0 ] && echo 'PASS' || ([ ${GATE_RC[G4]} -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo ""

# Overall result
if [ ${GATE_RC[G1]} -eq 0 ] && [ ${GATE_RC[G2]} -eq 0 ] && [ ${GATE_RC[G3]} -eq 0 ]; then
    echo "OVERALL: PASS (all critical gates)"
    exit 0
else
    echo "OVERALL: FAIL (one or more critical gates failed)"
    exit 1
fi
```
