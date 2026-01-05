## 🎯 La Propuesta Original

**Idea**: Crear un backend JSONL para session.md que permita:
- session.md = Log humano (puede crecer indefinidamente)
- session.jsonl = Log estructurado para queries
- CLI hook en `session append` genera ambos
- Nuevo comando `session query --type X --last N`

**Justificación**: Alineado con "context as tool", no es RAG, permite session escalable.

---
