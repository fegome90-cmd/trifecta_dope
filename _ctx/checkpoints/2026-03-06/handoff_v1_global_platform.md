# Handoff Prompt: V1 Global Platform Work Orders

## Estado Actual

**Plan**: Execute V1 Global Platform Work Orders Plan
**Estado**: ✅ Completado - 4 WOs creados y validados

---

## Lo Completado

1. **Epic E-V1** agregado a `_ctx/backlog/backlog.yaml`
   - Título: "Trifecta V1 Global Platform"
   - Prioridad: P0
   - WOs asociados: WO-0040, WO-0041, WO-0042, WO-0043

2. **4 Work Orders creados** en `_ctx/jobs/pending/`:
   - `WO-0040`: Roadmap Master (Tracking-Only) - P1
   - `WO-0041`: SSOT + Contratos + Skeleton - P0
   - `WO-0042`: CLI Adelgazado + Repo Commands - P0
   - `WO-0043`: SQLite + Daemon + Operación Real - P0

3. **Fixes aplicados** a problemas pre-existentes:
   - `WO-0018A.yaml`: Schema datetime malformado → corregido
   - `WO-0036.yaml`: Faltaba verify.commands → agregado
   - `backlog.yaml`: Referencia inválida a WO-0038 → eliminada

4. **Validación**: `ctx_backlog_validate.py --strict` ✅ PASA

5. **Contexto sincronizado**: `trifecta ctx sync --segment .` ✅

---

## Arquitectura del Plan V1

```
Principio: 0041 define → 0042 expone → 0043 opera

WO-0041: SSOT + Contratos + Skeleton
├── ADRs (SegmentRef SSOT, Platform Runtime, Native-first Layout)
├── segment_ref.py + repo_ref.py
├── resolve_segment_ref() - SINGLE SOURCE OF TRUTH
├── SegmentRef dataclass (frozen)
├── contracts.py, errors.py
└── tests/contracts/

WO-0042: CLI Adelgazado + Repo Commands
├── trifecta status --repo <path>
├── trifecta doctor --repo <path>
├── trifecta repo register/list/show
├── --json flag
└── Stable exit codes

WO-0043: SQLite + Daemon + Operación Real
├── repo_store.py (SQLite per-repo)
├── daemon_manager.py (start/stop/status/restart)
├── health.py
├── index_use_case.py, query_use_case.py
└── Recovery test (kill dirigido, no pkill)
```

---

## Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `_ctx/backlog/backlog.yaml` | Epic E-V1 con 4 WOs en cola |
| `_ctx/jobs/pending/WO-0040.yaml` | WO tracking (no ejecutable) |
| `_ctx/jobs/pending/WO-0041.yaml` | WO SSOT - iniciar por este |
| `_ctx/jobs/pending/WO-0042.yaml` | WO CLI - depende de 0041 |
| `_ctx/jobs/pending/WO-0043.yaml` | WO SQLite - depende de 0041, 0042 |

---

## Para Ejecutar los WOs

```bash
# 1. Validar que están listos
make wo-preflight WO=WO-0041

# 2. Tomar el primer WO
uv run python scripts/ctx_wo_take.py WO-0041

# 3. Trabajar en el worktree
cd .worktrees/WO-0041

# 4. Al terminar, cerrar
uv run python scripts/ctx_wo_finish.py WO-0041
```

---

## Verificación

- `ctx_backlog_validate.py --strict` debe pasar
- required_flow: `session.append:intent → ctx.sync → ctx.search → ctx.get → session.append:result → verify`
- Al cerrar: verificar SHA del commit, evidence en `_ctx/handoff/WO-XXXX/`

---

## Constraints

- Todos los WOs deben usar `epic_id: E-V1`
- Seguir WO schema v1
- Usar `resolve_segment_ref()` como SSOT
- No calcular repo_id manualmente
- Tests deben pasar antes de commit
