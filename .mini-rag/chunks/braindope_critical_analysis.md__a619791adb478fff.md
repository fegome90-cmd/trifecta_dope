### Alternativa C: SQLite en lugar de JSONL

**Idea**: `_ctx/session.db` (SQLite) en lugar de JSONL.

**Pros**:
- ✅ Queries rápidas con índices
- ✅ Schema evolution con migrations
- ✅ Transacciones (atomicidad)

**Contras**:
- ❌ No es "plain text" (menos debuggable)
- ❌ Añade dependencia (SQLite)

---
