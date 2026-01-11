==============================
# SUMMARY: Gate Results con RCs explícitos (AP7)
# ============================================================================
echo ""
echo "=== FINAL GATE RESULTS ==="
echo "G1 (pytest collecting): RC=$G1_RC ($([ $G1_RC -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G2 (path hygiene):      RC=$G2_OVERALL ($([ $G2_OVERALL -eq 0 ] && echo 'PASS' || echo 'FAIL'))"
echo "G3 (ast symbols):       RC=$G3_OVERALL ($([ $G3_OVERALL -eq 0 ] && echo 'PASS' || ([ $G3_OVERALL -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo "G4 (telemetry):         RC=$G4_OVERALL ($([ $G4_OVERALL -eq 0 ] && echo 'PASS' || ([ $G4_OVERALL -eq 255 ] && echo 'SKIP' || echo 'FAIL')))"
echo ""

# Overall result (AP7: FAIL-CLOSED)
if [ $G1_RC -eq 0 ] && [ $G2_OVERALL -eq 0 ] && [ $G3_OVERALL -eq 0 ]; then
    echo "OVERALL: PASS (all critical gates)"
    exit 0
else
    echo "OVERALL: FAIL (one or more critical gates failed)"
    exit 1
fi
```
