### ⏳ C) Implementar ctx.plan

**Objetivo**: Planificación usando SOLO PRIME (no RAG)

**Spec**:
```bash
trifecta ctx.plan --segment <path> --task "<texto>"
```

**C1) Fuente ÚNICA**: PRIME
- Leer `_ctx/prime_*.md`
- PRIME debe exponer:
  - `index.entrypoints`: puntos de entrada (paths + razón)
  - `index.feature_map`: feature → {chunk_ids, paths, keywords}

**C2) Salida JSON + legible**:
```json
{
  "selected_feature": "string|null",
  "plan_hit": true|false,
  "chunk_ids": ["chunk:abc", "chunk:def"],
  "paths": ["src/file.py", "docs/feature.md"],
  "next_steps": [
    {"action": "read", "target": "src/file.py"},
    {"action": "implement", "target": "function X"}
  ],
  "budget_est": {"tokens": 1500, "why": "2 chunks + implementation"}
}
```

**C3) Telemetría nueva**:
```json
{
  "event": "ctx.plan",
  "plan_hit": true|false,
  "selected_feature": "feature_name",
  "task_hash": "sha256(task)",
  "returned_chunks_count": 2,
  "returned_paths_count": 1,
  "latency_ms": 45
}
```

**Archivos a crear/modificar**:
- `src/application/plan_use_case.py` - Nuevo
- `src/infrastructure/cli.py` - Agregar comando `ctx plan`
- `_ctx/prime_trifecta_dope.md` - Agregar index.entrypoints y index.feature_map

---
