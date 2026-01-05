=============
# G1: pytest collecting (AP7: FAIL-CLOSED con RC explícito)
# ============================================================================
echo "=== G1: Pytest Collection ==="
echo "Running: uv run pytest --collect-only -q"

# AP6: Todo tee'd (no /dev/null)
uv run pytest --collect-only -q 2>&1 | tee "${ARTIFACTS}/g1_pytest_collect.txt"
G1_PIPESTATUS=(${PIPESTATUS[*]})
GATE_RC[G1]=${G1_PIPESTATUS[0]}

echo "G1_RC=${GATE_RC[G1]}" | tee -a "${ARTIFACTS}/g1_pytest_collect.txt"

# Detectar "ERROR collecting" en output
if grep -qi "ERROR collecting" "${ARTIFACTS}/g1_pytest_collect.txt"; then
    GATE_RC[G1]=1  # FAIL
    echo "Result: FAIL (ERROR collecting detected)"
else
    # AP7: RC explícito determina PASS/FAIL
    if [ ${GATE_RC[G1]} -eq 0 ]; then
        echo "Result: PASS (RC=0, no collection errors)"
    else
        echo "Result: FAIL (RC=${GATE_RC[G1]}, unknown error)"
    fi
fi
echo ""

# ============================================================================
# G2: Path Hygiene (AP6, AP7, AP10: sync debe pasar primero)
# ============================================================================
echo "=== G2: Path Hygiene Check ==="
echo "Running: uv run trifecta ctx sync -s ."

# AP6: stderr capturado (no /dev/null)
uv run trifecta ctx sync -s . 2>&1 | tee "${ARTIFACTS}/g2_ctx_sync.txt"
G2_SYNC_PIPESTATUS=(${PIPESTATUS[*]})
SYNC_RC=${G2_SYNC_PIPESTATU
