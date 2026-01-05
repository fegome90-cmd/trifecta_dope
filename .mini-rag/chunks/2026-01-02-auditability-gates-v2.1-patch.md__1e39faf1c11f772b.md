status --porcelain > "${ARTIFACTS}/git_status.txt" 2>&1
echo "Git SHA: $(cat ${ARTIFACTS}/git_sha.txt)"
echo "Git dirty: $(test -s ${ARTIFACTS}/git_status.txt && echo 'yes' || echo 'no')"
echo ""

# ============================================================================
# G1: pytest collecting (AP7: FAIL-CLOSED con RC explícito)
# ============================================================================
echo "=== G1: Pytest Collection ==="
echo "Running: uv run pytest --collect-only -q"

uv run pytest --collect-only -q 2>&1 | tee "${ARTIFACTS}/g1_pytest_collect.txt"
G1_RC=${PIPESTATUS[0]}

echo "G1_RC=$G1_RC" | tee -a "${ARTIFACTS}/g1_pytest_collect.txt"

if grep -qi "ERROR collecting" "${ARTIFACTS}/g1_pytest_collect.txt"; then
    G1_RC=1  # FAIL
    echo "Result: FAIL (ERROR collecting detected)"
else
    if [ $G1_RC -eq 0 ]; then
        echo "Result: PASS (RC=0, no collection errors)"
    else
        echo "Result: FAIL (RC=$G1_RC, unknown error)"
    fi
fi
echo ""

# ============================================================================
# G2: Path Hygiene (AP6, AP7, AP10: sync debe pasar primero)
# ============================================================================
echo "=== G2: Path Hygiene Check ==="
echo "Running: uv run trifecta ctx sync -s ."

uv run trifecta ctx sync -s . 2>&1 | tee "${ARTIFACTS}/g2_ctx_sync.txt"
G2_SYNC_RC=${PIPESTATUS[0]}

e
