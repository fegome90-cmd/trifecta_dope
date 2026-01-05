### Para G3 (ast symbols):
```bash
# Localizar resolver de sym://
rg -n "sym://|parse_sym|Symbol|FILE_NOT_FOUND|module.*resolve" src/

# Verificar cálculo de root en cli_ast
rg -n "resolve_segment_root|Path\(segment\)" src/infrastructure/cli_ast.py

# Probar diferentes símbolos (todos deben FILE_NOT_FOUND hoy)
uv run trifecta ast symbols sym://python/mod/use_cases 2>/dev/null | jq -r '.errors[0].code'
uv run trifecta ast symbols sym://python/mod/context_service 2>/dev/null | jq -r '.errors[0].code'

# Test tripwire: NO debe ser FILE_NOT_FOUND
uv run trifecta ast symbols sym://python/mod/context_service 2>/dev/null | jq -r '.status, .errors[0].code // "null"'
# Esperado después de fix: "ok" o código != "FILE_NOT_FOUND"
```

---
