```bash
# PASS/FAIL explícito:
if [ $AST_RC -eq 0 ] && [ "$STATUS" != "parse_error" ] && ([ "$STATUS" = "ok" ] || ([ "$STATUS" = "error" ] && [ "$CODE" != "FILE_NOT_FOUND" ])); then
    G3_OVERALL=0  # PASS
else
    G3_OVERALL=1  # FAIL
fi
```

**Por qué elimina PASS falso:**
- `jq` stdout se captura en archivo intermedio → variable (limpio)
- `jq` stderr se captura separado (no contamina STATUS/CODE)
- Si JSON no es parseable, `STATUS` contiene "parse_error" → FAIL explícito

---
