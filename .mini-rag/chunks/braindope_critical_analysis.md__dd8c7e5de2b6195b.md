### 5. **Query Performance con Crecimiento Indefinido**

**PROPUESTA**: "session puede crecer cuanto necesite el proyecto"

**PROBLEMA**: Un archivo JSONL de 10K entradas sin índices = búsqueda O(n).

**Escenario real**:
- 6 meses de proyecto = ~500 entradas
- `session query --type debug --last 5`
- Sin índice: Lee 500 líneas, filtra, retorna 5

**REALIDAD**: JSONL sin índices no escala bien. Necesitas:
- Índices externos (ej: SQLite)?
- Límites de tamaño (ej: 1000 entradas máx)?
- Archivado periódico (contradice "puede crecer cuanto necesite")?

**TRADE-OFF NO DISCUTIDO**: Escalabilidad vs Complejidad.

---
