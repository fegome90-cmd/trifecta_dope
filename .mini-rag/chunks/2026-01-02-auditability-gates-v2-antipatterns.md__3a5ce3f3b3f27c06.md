**Uso del script:**
```bash
# Ejecutar desde el repo
cd /path/to/trifecta_dope
bash audit_repro.sh

# Ver evidencia capturada
ls /tmp/trifecta_audit_*/

# Re-run gate individual (con RC preservado)
# G1:
uv run pytest --collect-only -q 2>&1 | tee /tmp/g1.log; echo "RC=${PIPESTATUS[0]}"
# G2:
uv run trifecta ctx sync -s . 2>&1 | tee /tmp/g2_sync.log; SYNC_RC=${PIPESTATUS[0]}; rg -n '"/Users/' _ctx/context_pack.json 2>&1 | tee /tmp/g2_rg.log; echo "SYNC=$SYNC_RC, RG=$?"
# G3:
uv run trifecta ast symbols sym://python/mod/context_service 2>&1 | tee /tmp/g3.log; jq -r '.status, .errors[0].code // "null"' /tmp/g3.log
```

---
