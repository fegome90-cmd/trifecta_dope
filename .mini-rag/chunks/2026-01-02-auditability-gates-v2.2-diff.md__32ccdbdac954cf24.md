**Por qué elimina PASS falso:**
- `mode="json"` convierte Path objects a strings antes de sanitización
- Previene `TypeError: Object of type Path is not JSON serializable`
- Garantiza que `sanitized_dump()` nunca lanza excepción por serialización

---
