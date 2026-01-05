==========
echo "=== G1: Pytest Collection ==="
echo "Running: uv run pytest --collect-only -q"
uv run pytest --collect-only -q > "${ARTIFACTS}/pytest_collect.txt" 2>&1
G1_RC=$?
echo "G1_RC=$G1_RC" | tee -a "${ARTIFACTS}/pytest_collect.txt"

# Detectar "ERROR collecting" en output
if grep -qi "ERROR collecting" "${ARTIFACTS}/pytest_collect.txt"; then
    GATE_RC[G1]=1  # FAIL
    echo "Result: FAIL (ERROR collecting detected)"
else
    GATE_RC[G1]=0  # PASS
    echo "Result: PASS (no collection errors)"
fi
echo ""

# ============================================================================
# G2: Path Hygiene (FAIL-CLOSED: matches encontrados = FAIL)
# ============================================================================
echo "=== G2: Path Hygiene Check ==="
echo "Running: uv run trifecta ctx sync -s ."
uv run trifecta ctx sync -s . > "${ARTIFACTS}/ctx_sync.log" 2>&1
SYNC_RC=$?
echo "Sync RC=$SYNC_RC" | tee -a "${ARTIFACTS}/ctx_sync.log"

echo "Checking for PII/absolute paths..."
rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json > "${ARTIFACTS}/pii_check.txt" 2>&1
G2_RG_RC=$?
echo "rg RC=$G2_RG_RC" | tee "${ARTIFACTS}/pii_rc.txt"

# rg retorna 1 cuando NO hay matches (EXITO para nosotros)
if [ $G2_RG_RC -eq 1 ]; then
    GATE_RC[G2]=0  # PASS
    echo "Result: PASS (no PII found)"
else
    GATE_RC[G2]=1  # FAIL
    echo "Result: FAIL (PII found)"
    echo "Matche
