**Uso del script:**
```bash
# Ejecutar desde el repo
cd /path/to/trifecta_dope
bash audit_repro.sh

# Ver evidencia capturada
ls /tmp/trifecta_audit_*/

# Re-run gate individual
# G1:
uv run pytest --collect-only -q 2>&1 | grep -i "ERROR collecting" && echo "FAIL" || echo "PASS"
# G2:
uv run trifecta ctx sync -s . >/dev/null 2>&1 && rg -n '"/Users/' _ctx/context_pack.json; echo "RC=$? (1=PASS)"
# G3:
uv run trifecta ast symbols sym://python/mod/context_service 2>/dev/null | jq -r '.status, .errors[0].code // "null"'
```

---
