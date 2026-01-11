## 📊 Scorecard de Riesgos

| Riesgo | Severidad | Mitigación |
|:-------|:----------|:-----------|
| Duplicación con telemetry | 🔴 Alta | Unificar o justificar separación |
| Sincronización .md/.jsonl | 🔴 Alta | Single source of truth |
| Background script fragility | 🟡 Media | Hook síncrono o supervisor |
| Schema drift | 🟡 Media | Versionado explícito |
| Query performance | 🟢 Baja | Límites de tamaño o índices |
| Tool use detection | 🟡 Media | Manual primero, auto después |

---

**Conclusión**: La idea tiene mérito, pero necesita más diseño. No es un "green light" automático.
