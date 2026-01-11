q falló)
    if [ -z "$G3_STATUS" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (jq parsing failed, STATUS empty)"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq_stderr.txt"
    elif [ "$G3_STATUS" = "parse_error" ] || [ "$G3_STATUS" = "null" ]; then
        G3_OVERALL=1  # FAIL
        echo "Result: FAIL (JSON invalid or status is null)"
        echo "Raw JSON:"
        cat "${ARTIFACTS}/g3_ast.json"
        echo "jq stderr:"
        cat "${ARTIFACTS}/g3_jq_stderr.txt"
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
fi
echo ""
```
