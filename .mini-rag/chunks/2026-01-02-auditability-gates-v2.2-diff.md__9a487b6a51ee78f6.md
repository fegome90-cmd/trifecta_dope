```bash
# ============================================================================
# G3: ast symbols (AP1, AP6, AP7: parse_error = FAIL, variables limpias)
# ============================================================================
echo "=== G3: AST Symbols Command ==="
echo "Running: uv run trifecta ast symbols sym://python/mod/context_service"

# v2.2 FIX: stdout y stderr separados desde el inicio
uv run trifecta ast symbols sym://python/mod/context_service \
    > "${ARTIFACTS}/g3_ast.json" \
    2> "${ARTIFACTS}/g3_ast.stderr"
G3_AST_RC=$?

echo "Command RC=$G3_AST_RC" | tee "${ARTIFACTS}/g3_ast_rc.txt"

# v2.2 FIX: jq stdout → archivo → variable (limpio)
if command -v jq &> /dev/null; then
    # STATUS: jq stderr → archivo separado
    jq -r '.status' "${ARTIFACTS}/g3_ast.json" \
        > "${ARTIFACTS}/g3_status.txt" \
        2> "${ARTIFACTS}/g3_jq_stderr.txt"
    G3_STATUS=$(cat "${ARTIFACTS}/g3_status.txt")

    # CODE: jq stderr → mismo archivo (append)
    jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast.json" \
        > "${ARTIFACTS}/g3_code.txt" \
        2>> "${ARTIFACTS}/g3_jq_stderr.txt"
    G3_CODE=$(cat "${ARTIFACTS}/g3_code.txt")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_CODE" | tee -a "${ARTIFACTS}/g3_ast_rc.txt"

    # v2.2 FIX: Validar que STATUS no esté vacío (jq falló)
    if [ -z "$G3_STATUS" ]; then
        G3_OVERALL=1  # FAIL
