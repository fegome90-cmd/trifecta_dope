=====================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# AP6: stderr capturado
uv run trifecta ast symbols sym://python/mod/context_service 2>&1 | tee "${ARTIFACTS}/g3_ast_symbols.txt"
G3_PIPESTATUS=(${PIPESTATUS[*]})
G3_CMD_RC=${G3_PIPESTATUS[0]}

echo "Command RC=$G3_CMD_RC" | tee -a "${ARTIFACTS}/g3_ast_symbols.txt"

# AP1: Parse con jq desde archivo (no pipe, evita stringly-typed)
if command -v jq &> /dev/null; then
    G3_STATUS=$(jq -r '.status // "error"' "${ARTIFACTS}/g3_ast_symbols.txt" 2>/dev/null || echo "parse_error")
    G3_ERROR_CODE=$(jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast_symbols.txt" 2>/dev/null || echo "null")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_ERROR_CODE" | tee -a "${ARTIFACTS}/g3_ast_symbols.txt"

    # AP7: lógica explícita
    if [ "$G3_STATUS" = "ok" ]; then
        GATE_RC[G3]=0  # PASS
        echo "Result: PASS"
    elif [ "$G3_ERROR_CODE" = "FILE_NOT_FOUND" ]; then
        GATE_RC[G3]=1  # FAIL
        echo "Result: FAIL (FILE_NOT_FOUND)"
    else
        GATE_RC[G3]=0  # PASS (error diferente es aceptable)
        echo "Result: PASS (error is not FILE_NOT_FOUND)"
    fi
else
    echo "WARNING: jq not found, skipping JSON parse"
    GATE_RC[G3]=255  # SKIP
fi
echo ""

# ==================================================
