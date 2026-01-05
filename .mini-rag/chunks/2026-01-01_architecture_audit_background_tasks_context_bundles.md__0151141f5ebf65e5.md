### 5.3 Riesgo R3: Multi-Writer Corruption (context_pack.json)

**Descripción**: Dos `trifecta ctx build` concurrentes escriben a `context_pack.json` sin lock.

**Impacto**: CRÍTICO (pack corrupto → validation FAIL → pipeline blocked).

**Probabilidad**: BAJA en MVP (uso single-agent), ALTA en multi-agent future.

**Mitigación**:
1. **Preventivo**: Agregar lockfile `_ctx/context_pack.lock` (fcntl.LOCK_EX) en `BuildContextPackUseCase`.
2. **Detective**: Validar SHA256 de pack después de write, retry si mismatch.
3. **Correctivo**: Si lock busy > 30s, fail con error `Another build in progress`.
4. **Validación**: Test `test_concurrent_builds_block` con multiprocessing.

**Métrica**: `build_lock_contention_count` (cuántas veces se esperó lock).

---
