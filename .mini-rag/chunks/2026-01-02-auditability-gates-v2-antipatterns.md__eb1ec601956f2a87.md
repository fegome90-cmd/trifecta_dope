txt"
G2_SYNC_PIPESTATUS=(${PIPESTATUS[*]})
SYNC_RC=${G2_SYNC_PIPESTATUS[0]}

echo "Sync RC=$SYNC_RC" | tee -a "${ARTIFACTS}/g2_ctx_sync.txt"

echo "Checking for PII/absolute paths..."
# AP6: Todo tee'd
rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json 2>&1 | tee "${ARTIFACTS}/g2_rg_pii.txt"
G2_RG_PIPESTATUS=(${PIPESTATUS[*]})
RG_RC=${G2_RG_PIPESTATUS[0]}

echo "rg RC=$RG_RC" | tee "${ARTIFACTS}/g2_rg_rc.txt"

# AP7: lógica explícita de PASS/FAIL
# AP10: sync debe pasar primero
if [ $SYNC_RC -ne 0 ]; then
    GATE_RC[G2]=1  # FAIL
    echo "Result: FAIL (sync failed, RC=$SYNC_RC)"
else
    # rg retorna 1 cuando NO hay matches (EXITO para nosotros)
    if [ $RG_RC -eq 1 ]; then
        GATE_RC[G2]=0  # PASS
        echo "Result: PASS (sync ok, no PII found)"
    else
        GATE_RC[G2]=1  # FAIL
        echo "Result: FAIL (PII found, RG_RC=$RG_RC)"
        echo "Matches:"
        cat "${ARTIFACTS}/g2_rg_pii.txt"
    fi
fi
echo ""

# Sample context_pack.json para inspección visual
echo "Sample context_pack.json (first 30 lines):"
head -30 _ctx/context_pack.json | tee "${ARTIFACTS}/g2_context_pack_sample.txt"
echo ""

# ============================================================================
# G3: ast symbols (AP1: jq parse desde archivo, AP6: stderr capturado)
# ============================================================================
echo "=== G3: AST Symbols Comman
