## Overview

El Context Pack es un sistema de 3 capas para ingestión token-optimizada de documentación Markdown hacia LLMs. Permite cargar contexto eficiente sin inyectar textos completos en cada prompt.

```
┌─────────────────────────────────────────────────────────────┐
│  Context Pack (context_pack.json)                           │
├─────────────────────────────────────────────────────────────┤
│  Digest    → Siempre en prompt (~10-30 líneas)              │
│  Index     → Siempre en prompt (referencias de chunks)       │
│  Chunks    → Bajo demanda vía tool (texto completo)          │
└─────────────────────────────────────────────────────────────┘
```

---
