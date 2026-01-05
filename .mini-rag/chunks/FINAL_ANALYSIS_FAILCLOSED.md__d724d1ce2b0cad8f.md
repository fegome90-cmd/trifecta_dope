### BLOCKER #8: Backward Compatibility de Output
**Causa**: Propuesta cambia output de text a JSON → rompe scripts que parsean  
**Evidencia**: AUDIT:L125-L151  
**Fix mínimo**: Mantener output text + añadir opcional `(entry: session:ID)`  
**Test/Gate**: Verificar que output sigue siendo text, NO JSON

**Output actual** (debe mantenerse):
```
✅ Appended to _ctx/session_trifecta_dope.md
   Summary: <text>
```

**Output propuesto ERRÓNEO** (rompe compat):
```json
{"status": "ok", "message": "...", "entry_id": "..."}
```

**Fix**:
```
✅ Appended to _ctx/session_trifecta_dope.md (entry: session:abc123)
   Summary: <text>
```

---
