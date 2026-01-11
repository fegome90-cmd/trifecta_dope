**NOTAS SOBRE RCs (AP7, corregido):**
- G1: `G1_RC=0` → PASS; `G1_RC≠0` → FAIL
- G2: `SYNC_RC=0` AND `RG_RC=1` → PASS; else → FAIL
- G3: `AST_RC=0` AND `STATUS≠parse_error` AND (`STATUS=ok` OR `CODE≠FILE_NOT_FOUND`) → PASS; else → FAIL

**CAMBIOS desde v2.0:**
- G2: `PIPESTATUS[0]` explícito (no `$?` de tee)
- G3: stdout→.json, stderr→.stderr (separados); `parse_error` tratado como FAIL

---
