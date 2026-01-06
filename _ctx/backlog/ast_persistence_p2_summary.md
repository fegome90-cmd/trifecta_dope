# AST Persistence P2 Summary

**Date**: 2026-01-06  
**Epic**: E-0001 (AST Cache Operability)

---

## Completed Work Orders

### WO-P2.1: Telemetry Integration ✅ COMPLETE
**SHA**: `e323433`  
**Status**: Production Ready

**Deliverables**:
- `TelemetryAstCache` wrapper (decorator pattern)
- Factory wiring (`get_ast_cache(telemetry=...)`)
- CLI + PR2 integration
- E2E tests (3/3 PASSED)

**Events Emitted**:
```json
{
  "cmd": "ast.cache.hit|miss|write",
  "args": {"cache_key": "..."},
  "result": {"backend": "SQLiteCache|InMemoryLRUCache", "segment_id": "..."},
  "timing_ms": 2
}
```

**Impact**: Observability operacional para debugging y análisis de performance.

---

### WO-P2.2: File Locks ❌ CANCELLED
**SHA**: `ab4beea`  
**Status**: Not Needed

**Rationale**:
- SQLite WAL mode ya maneja concurrencia correctamente
- RED test (40 concurrent writes) pasó sin corruption
- Implementación complexity >> benefit
- WO-P2.1 (telemetry) entrega observabilidad crítica

**Recommendation**: Monitorear telemetría en producción. Reevaluar locks solo si aparece contención real.

---

## Roadmap Remaining (P2 Original Plan)

### P2.3: Corruption Detection & Recovery (BACKLOG)
**Priority**: P2  
**Status**: Deferred

**Scope**:
- `PRAGMA integrity_check` on DB load
- Auto-recovery (delete corrupted DB, rebuild)
- Telemetry: `ast.cache.corruption_detected`

**Trigger**: Producción reports corruption incidents

---

### P2.4: Resource Monitoring (BACKLOG)
**Priority**: P3  
**Status**: Deferred

**Scope**:
- DB size warnings (> 500MB)
- Entry count/age stats
- Telemetry: `ast.cache.size_warning`

**Trigger**: Telemetría muestra DBs > 100MB en wild

---

### P2.5: TTL & Eviction (BACKLOG)
**Priority**: P3  
**Status**: Deferred

**Scope**:
- `file_mtime` column para invalidación automática
- Cleanup periódico (entries > 7 days)

**Trigger**: Cache pollution detectado en producción

---

## Production Readiness

**Current State**: ✅ PRODUCTION READY

- [x] P0: Inventory complete
- [x] P1: Factory wiring + env var control
- [x] P2.1: Audit-grade telemetry
- [x] E2E tests (10/10 PASSED)
- [x] Walkthrough con evidencia

**Enable Global**:
```bash
export TRIFECTA_AST_PERSIST=1
```

**Monitor**:
```bash
jq 'select(.cmd | startswith("ast.cache"))' _ctx/telemetry/events.jsonl
```

---

## Success Metrics (Target)

After 30 days in production:

- [ ] Cache hit rate > 60%
- [ ] Zero corruption incidents
- [ ] DB size < 100MB per segment
- [ ] P95 latency < 10ms (get operations)

---

## Lessons Learned

1. **TDD RED-first caught premature optimization**: SQLite ya protege concurrencia.
2. **Telemetry > Locks**: Observabilidad es más valiosa que control explícito.
3. **Context managers > nested functions**: Simpler pattern para wrapping.
4. **Fail-closed tests**: E2E cross-process tests son críticos para persistence.
