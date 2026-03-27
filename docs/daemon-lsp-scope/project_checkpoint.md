# Checkpoint: Subsistema Daemon + LSP

**Fecha**: 2026-03-22 | **Estado**: Daemon core cerrado localmente

---

## Checklist del proyecto

### Scope + Plan

- [x] Scope CLOOP completado (5 secciones + 7 anexos)
- [x] Contrato oficial creado (daemon_contract.md)
- [x] Plan v2 creado y aprobado (5 fases)
- [x] Plan de deuda técnica creado

### Fase 1: Autoridad

- [x] Contrato documentado
- [x] CONTRACTS.md actualizado
- [x] lsp_daemon.py marcado como REFERENCE
- [x] lsp_manager.py marcado como STUB

### Fase 2: Veracidad

- [x] runtime.db eliminado del health check
- [x] DEFAULT_TTL unificado (300s)
- [x] Telemetry daemon_status agregado

### Fase 3: Integración LSP

- [x] LSPClient integrado en daemon_run
- [x] Envelope JSON funcionando
- [x] Fallback explícito con lsp_contracts.py
- [x] HEALTH incluye LSP state

### Fase 4: Hardening

- [x] Singleton locking agregado
- [x] TTL opcional via env var

### Fase 5: Deprecación

- [x] lsp_manager.py marcado como DEPRECATED
- [x] lsp_daemon.py verificado como REFERENCE

### Reviews + Audits

- [x] Code review plan (Approved)
- [x] Code review implementación (Approved)
- [x] Code review comprehensivo (Approved)
- [x] Auditoría v1 completada
- [x] Auditoría v2 (endurecida)
- [x] Review del plan de validación

### Validación

- [x] V1: pytest (22 passed)
- [x] V2: health (100% con daemon)
- [x] V3: singleton (1 daemon)
- [x] V4: TTL (implementado, no validado con timeout)
- [ ] V5: LSP envelope (requiere pyright)

### Cierre

- [x] Batch daemon core cerrado
- [x] Memo final corregido
- [x] Checkpoint creado

---

## Pendientes no bloqueantes (micro-batch independiente)

- [ ] Validar TTL con timeout real
- [ ] Verificar telemetry events.jsonl
- [ ] Validar LSP con pyright instalado

---

## Archivos de código modificados

| Archivo | Cambio |
|---------|--------|
| `src/infrastructure/lsp_daemon.py` | REFERENCE + DEFAULT_TTL=300 |
| `src/application/lsp_manager.py` | DEPRECATED |
| `src/platform/health.py` | Eliminado runtime.db check |
| `src/infrastructure/cli.py` | Telemetry + LSPClient + envelope JSON + TTL |
| `src/platform/daemon_manager.py` | Singleton locking + TTL env var |
| `docs/CONTRACTS.md` | Referencia daemon contract |
