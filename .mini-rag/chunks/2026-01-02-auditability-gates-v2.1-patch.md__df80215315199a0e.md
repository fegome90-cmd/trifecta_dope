ados
uv run trifecta ast symbols sym://python/mod/context_service \
    > "${ARTIFACTS}/g3_ast.json" \
    2> "${ARTIFACTS}/g3_ast.stderr"
G3_AST_RC=$?

echo "Command RC=$G3_AST_RC" | tee "${ARTIFACTS}/g3_ast_rc.txt"

# AP1: Parse con jq desde archivo
# AP6: jq stderr capturado (no 2>/dev/null)
if command -v jq &> /dev/null; then
    G3_STATUS=$(jq -r '.status // "parse_error"' "${ARTIFACTS}/g3_ast.json" 2>&1 | tee "${ARTIFACTS}/g3_jq.log")
    G3_CODE=$(jq -r '.errors[0].code // "null"' "${ARTIFACTS}/g3_ast.json" 2>&1 | tee -a "${ARTIFACTS}/g3_jq.log")

    echo "Parsed: status=$G3_STATUS, error_code=$G3_CODE" | tee -a "${ARTIFACTS}/g3_ast_rc.txt"

    # AP7: parse_error es FAIL (fail-closed)
    if [ "$G3_STATUS" = "parse_error" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (JSON parse error)"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq.log"
        echo "Command stderr:"
        cat "${ARTIFACTS}/g3_ast.stderr"
    elif [ "$G3_STATUS" = "ok" ]; then
        G3_OVERALL=0  # PASS
        echo "Result: PASS"
    elif [ "$G3_CODE" = "FILE_NOT_FOUND" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (FILE_NOT_FOUND)"
    else
        G3_OVERALL=0  # PASS (error diferente es aceptable)
        echo "Result: PASS (error is not FILE_NOT_FOUND)"
    fi
else
    echo "WARNING: jq not found, skipping JSON parse"
    G3_OVERALL=255  # SKIP
f
