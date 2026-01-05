### 2. **Sincronización session.md ↔ session.jsonl**

**PROBLEMA**: Ahora tienes DOS fuentes de verdad que deben estar sincronizadas.

**Escenarios de fallo**:
- ✅ session.md escrito, ❌ JSONL falla → Pérdida de metadata estructurada
- ❌ session.md falla, ✅ JSONL escrito → Inconsistencia humano vs máquina
- ⚠️ Script background muere → ¿Cuántas entradas se pierden?

**PREGUNTA SIN RESPUESTA**: ¿Cuál es el source of truth? Si difieren, ¿a cuál crees?

**SOLUCIÓN POSIBLE**: Hacer que session.md sea generado DESDE el JSONL (single source of truth). Pero eso invierte la arquitectura.

---
