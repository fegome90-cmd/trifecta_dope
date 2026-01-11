### BLOCKER #7: Privacy Tests Ausentes
**Causa**: No hay test automatizado que valide no-leak de paths absolutos  
**Evidencia**: AUDIT:L517-L571  
**Fix mínimo**: Crear acceptance test con regex `/Users/|/home/|C:\\Users\\`  
**Test/Gate**: `pytest tests/acceptance/test_no_privacy_leaks.py::test_session_query_no_absolute_paths -v`

---
