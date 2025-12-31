### ❌ Patrones que NO Importamos

- **Redis**: Prematuro. Usamos SQLite local.
- **SARIF**: Es para findings, no para context data.
- **LLM Orchestration**: No llamamos LLM en ingest.
- **Multi-agent IPC**: No tenemos múltiples agentes.
- **Intelligent Router**: No hay routing (solo ingest).
- **Concurrent Processing**: Prematuro para 5 archivos pequeños.

---
