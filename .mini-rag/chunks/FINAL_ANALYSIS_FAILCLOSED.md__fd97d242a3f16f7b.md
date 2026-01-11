### BLOCKER #2: JSON Schema en Archivos Separados
**Causa**: Schema solo existe en markdown (SCOOP), no como `.schema.json` validable  
**Evidencia**: AUDIT:L153-L156, L188-L190  
**Fix mínimo**: Crear `docs/schemas/session_query_clean.schema.json` + validator test  
**Test/Gate**: `pytest tests/integration/test_session_query_schema.py -v`

---
