&1 | tee "${ARTIFACTS}/g2_ctx_sync.txt"
G2_SYNC_RC=${PIPESTATUS[0]}

echo "Sync RC=$G2_SYNC_RC" | tee -a "${ARTIFACTS}/g2_ctx_sync.txt"

echo "Checking for PII/absolute paths..."
rg -n '"/Users/|"/home/|file://' _ctx/context_pack.json 2>&1 | tee "${ARTIFACTS}/g2_rg_pii.txt"
G2_RG_RC=${PIPESTATUS[0]}

echo "rg RC=$G2_RG_RC" | tee "${ARTIFACTS}/g2_rg_rc.txt"

# AP7: lógica explícita de PASS/FAIL
if [ $G2_SYNC_RC -ne 0 ]; then
    G2_OVERALL=1  # FAIL
    echo "Result: FAIL (sync failed, RC=$G2_SYNC_RC)"
else
    if [ $G2_RG_RC -eq 1 ]; then
        G2_OVERALL=0  # PASS
        echo "Result: PASS (sync ok, no PII found)"
    else
        G2_OVERALL=1  # FAIL
        echo "Result: FAIL (PII found, RG_RC=$G2_RG_RC)"
        echo "Matches:"
        cat "${ARTIFACTS}/g2_rg_pii.txt"
    fi
fi
echo ""

# Sample context_pack.json
echo "Sample context_pack.json (first 30 lines):"
head -30 _ctx/context_pack.json | tee "${ARTIFACTS}/g2_context_pack_sample.txt"
echo ""

# ============================================================================
# G3: ast symbols (AP1, AP6, AP7: parse_error = FAIL)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# G3 v2.1: stdout/stderr separados
uv run trifecta ast symbols sym://python/mod/context_service \
