**NOTAS SOBRE RCs (AP7):**
- G1: RC=0 → PASS (collect ok); RC≠0 → FAIL
- G2: `SYNC_RC=0` AND `RG_RC=1` → PASS (sync ok + no matches); else → FAIL
- G3: `STATUS=ok` OR (`STATUS=error` AND `CODE≠FILE_NOT_FOUND`) → PASS; else → FAIL

---
