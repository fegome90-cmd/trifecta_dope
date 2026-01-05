### Alternativa B: Session.md como Single Source + Generator

**Idea**: session.md es el único source of truth. Script genera .jsonl DESDE .md.

**Pros**:
- ✅ No hay problema de sincronización
- ✅ session.md sigue siendo append-only

**Contras**:
- ❌ Parsing de markdown = frágil
- ❌ Estructura del .md debe ser estricta

---
