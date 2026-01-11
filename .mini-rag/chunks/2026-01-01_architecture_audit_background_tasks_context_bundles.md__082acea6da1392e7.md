### 5.4 Riesgo R4: Stale Locks

**Descripción**: Proceso crashea sin liberar lock, dejando `task.lock` stale forever.

**Impacto**: MEDIO (task bloqueada, requiere manual cleanup).

**Probabilidad**: MEDIA (crashes son raros pero no imposibles).

**Mitigación**:
1. **Preventivo**: Lockfile con timestamp + PID, TTL de 1hr.
2. **Detective**: `trifecta background ps` detecta locks > 1hr y marca como STALE.
3. **Correctivo**: Comando `trifecta background cleanup` elimina locks stale (after confirming PID dead).
4. **Validación**: Test `test_stale_lock_cleanup_after_1hr`.

**Métrica**: `stale_lock_cleanup_count` (cuántos locks fueron limpiados).

---
