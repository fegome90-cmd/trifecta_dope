_RC[G2]=1  # FAIL
    echo "Result: FAIL (PII found)"
    echo "Matches:"
    cat "${ARTIFACTS}/pii_check.txt"
fi
echo ""

# Sample context_pack.json para inspección visual
echo "Sample context_pack.json (first 30 lines):"
head -30 _ctx/context_pack.json > "${ARTIFACTS}/context_pack_sample.txt"
cat "${ARTIFACTS}/context_pack_sample.txt"
echo ""

# ============================================================================
# G3: ast symbols (FAIL-CLOSED: FILE_NOT_FOUND = FAIL)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"
uv run trifecta ast symbols sym://python/mod/context_service > "${ARTIFACTS}/ast_symbols_output.txt" 2>&1
G3_CMD_RC=$?
echo "Command RC=$G3_CMD_RC" | tee -a "${ARTIFACTS}/ast_symbols_output.txt"

# Parsear response
G3_STATUS=$(jq -r '.status // "error"' "${ARTIFACTS}/ast_symbols_output.txt" 2>/dev/null || echo "parse_error")
G3_ERROR_CODE=$(jq -r '.errors[0].code // "null"' "${ARTIFACTS}/ast_symbols_output.txt" 2>/dev/null || echo "null")

echo "Parsed: status=$G3_STATUS, error_code=$G3_ERROR_CODE"

if [ "$G3_STATUS" = "ok" ]; then
    GATE_RC[G3]=0  # PASS
    echo "Result: PASS"
elif [ "$G3_ERROR_CODE" = "FILE_NOT_FOUND" ]; then
    GATE_RC[G3]=1  # FAIL
    echo "Result: FAIL (FILE_NOT_FOUND)"
else
    GATE_RC[
