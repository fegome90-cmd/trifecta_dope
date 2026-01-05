**Por qué elimina PASS falso:**
- Variables STATUS/CODE se leen de archivos intermedios (no de pipe)
- Si `jq` falla, `STATUS` está vacío → detectado como FAIL
- `jq` stderr no contamina variables principales

---
